from typing import TYPE_CHECKING, List, Optional

from anyio.abc import TaskStatus

# noinspection PyProtectedMember
from pydantic import Field, PrivateAttr

from prefect.utilities.asyncutils import run_sync_in_worker_thread
from prefect.utilities.dockerutils import get_prefect_image_name
from prefect.workers.base import (
    BaseJobConfiguration,
    BaseVariables,
    BaseWorker,
    BaseWorkerResult,
)

if TYPE_CHECKING:
    from prefect.client.schemas import FlowRun


class CoiledWorkerJobConfiguration(BaseJobConfiguration):
    image: str = Field(
        default_factory=get_prefect_image_name,
        description="The image reference of a container image to use for created jobs. "
        "If not set, the latest Prefect image will be used.",
        examples=["docker.io/prefecthq/prefect:3-latest"],
    )
    region: Optional[str] = Field(
        default=None,
        description="The region in which to run the job on Coiled; by default uses default region from Coiled workspace",
    )

    vm_types: Optional[List[str]] = Field(default=None)
    # arm: Optional[bool] = Field(default=None)
    cpu: Optional[int] = Field(default=None)
    memory: Optional[str] = Field(default=None)
    gpu: Optional[bool] = Field(default=None)

    _job_name: str = PrivateAttr(default=None)


class CoiledVariables(BaseVariables):
    image: str = Field(
        default_factory=get_prefect_image_name,
        description="The image reference of a container image to use for created jobs. "
        "If not set, the latest Prefect image will be used.",
        examples=["docker.io/prefecthq/prefect:3-latest"],
    )
    region: Optional[str] = Field(
        default=None,
        description="The region in which to run the job on Coiled",
    )

    vm_types: Optional[List[str]] = Field(default=None)
    # arm: Optional[bool] = Field(default=None)  # TODO https://github.com/coiled/platform/issues/7530
    cpu: Optional[int] = Field(default=None)
    memory: Optional[str] = Field(default=None)
    gpu: Optional[bool] = Field(default=None)


class CoiledWorkerResult(BaseWorkerResult):
    """
    The result of a Cloud Run worker V2 job.
    """


class CoiledWorker(BaseWorker):
    """
    The Cloud Run worker V2.
    """

    type = "coiled"
    job_configuration = CoiledWorkerJobConfiguration
    job_configuration_variables = CoiledVariables
    _description = "Execute flow runs via Coiled."  # noqa
    _display_name = "Coiled"
    _documentation_url = "https://docs.prefect.io/integrations/TODO"
    _logo_url = "https://docs.coiled.io/_static/Coiled-Logo.svg"  # noqa

    async def run(
        self,
        flow_run: "FlowRun",
        configuration: CoiledWorkerJobConfiguration,
        task_status: Optional[TaskStatus] = None,
    ) -> CoiledWorkerResult:
        """
        Runs the flow run on Coiled and waits for it to complete.

        Args:
            flow_run: The flow run to run.
            configuration: The configuration for the job.
            task_status: The task status to update.

        Returns:
            The result of the job.
        """
        logger = self.get_flow_run_logger(flow_run)

        from coiled.batch import run, wait_for_job_done

        # clean up labels so they can be applied as Coiled tags
        tags = (
            {
                key.replace("prefect.io/", ""): val
                for key, val in configuration.labels.items()
            }
            if configuration.labels
            else {}
        )

        # submit the job to run on Coiled
        run_info = run(
            command=configuration.command,
            container=configuration.image,
            secret_env=configuration.env,
            region=configuration.region,
            vm_type=configuration.vm_types,
            # arm=configuration.arm,  # TODO https://github.com/coiled/platform/issues/7530
            cpu=configuration.cpu,
            memory=configuration.memory,
            gpu=configuration.gpu,
            tag=tags,
            logger=logger,
        )
        job_id = run_info.get("job_id")
        identifier = str(job_id)

        if task_status:
            task_status.started(identifier)

        # wait for Coiled job to be done
        job_state = await run_sync_in_worker_thread(wait_for_job_done, job_id=job_id)

        return CoiledWorkerResult(
            status_code=-1 if "error" in job_state else 0,
            identifier=identifier,
        )
