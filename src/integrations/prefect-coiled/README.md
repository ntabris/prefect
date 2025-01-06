# `prefect-coiled`

Prefect worker for running flows on Coiled.

## Installation

To start using `prefect-coiled`:

```bash
pip install prefect-coiled  # or `pip -e .` install from source 
```

## Starting a worker

When running a local worker, you can either have the worker implicitly pick up the Coiled API token
(from your local Coiled config file or environment variables),
or you can specify the API token using a Prefect credentials block for the work pool.

### Local worker with locally configured Coiled API token

If you're using local Coiled credentials for a worker that will run locally, you can start the worker like this:

```bash
prefect worker start -p "my-coiled-pool" --type "coiled"
```

### Coiled API token specified through Prefect credentials block

Things are more complicated if you need to specify the Coiled API token to use for the work pool.

You'll need to create a credentials block, like so:

```python
from prefect_coiled import CoiledCredentials

CoiledCredentials(api_token=api_token).save("coiled-creds")
```

You then create the work pool:

```bash
prefect work-pool create --type coiled my-coiled-pool
```

This will return a URL to the work pool. Follow this URL, click the "..." menu and select "Edit".
Find the "CoiledCredentials" field and select the "coiled-creds" that you created before creating the work pool.
Save the pool.

Now, you can start a worker for this pull and it will use the credentials from the credentials block when the worker uses Coiled:

```bash
prefect worker start -p "my-coiled-pool"
```

## Create a deployment from a flow

Then you can create a deployment which uses this pool by running something like this:

```python
from prefect import flow, task
from prefect.docker import DockerImage

@task
def foo(n):
    return n**2

@task
def do_something(x):
    print(x)

@flow(log_prints=True)
def my_flow():
    print("Hello from your Prefect flow!")
    X = foo.map(list(range(10)))
    do_something(X)
    return X

if __name__ == "__main__":
    arch = "amd64"
    my_flow.deploy(
        name="my-coiled-deploy",
        work_pool_name="my-coiled-pool",
        image=DockerImage(name="prefect-docker-image", tag=arch, platform=f"linux/{arch}"),
        job_variables={"memory": "16GiB"},  # use VM with 16GiB of memory for this flow
    )
```

## Run the flow

```bash
prefect deployment run 'my-flow/my-coiled-deploy'
```
