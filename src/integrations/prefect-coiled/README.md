# `prefect-coiled`

Prefect worker for running flows on Coiled.

## Installation

To start using `prefect-coiled`:

```bash
pip install prefect-coiled  # or `pip -e .` install from source 
```

If you haven't used Coiled before, you'll need to create a Coiled account and log in:

```bash
coiled login
```
and then connect Coiled to your cloud account (AWS, Google Cloud, or Azure) where Coiled will run your flows.
You can either use our interactive setup CLI:

```bash
coiled setup
```

or via the web app UI at https://cloud.coiled.io/settings/setup

## Starting a worker

The worker polls a work pool for pending Prefect flows and then uses Coiled to run the flow in the cloud.

When running the worker, you can either have the worker implicitly pick up your Coiled API token
(from your local Coiled config file or environment variables),
or you can specify the API token using a Prefect credentials block set for the work pool.

### Locally configured Coiled API token

If you've already used the Coiled CLI or Python API, you're probably already logged in locally,
and a locally running Coiled Prefect worker will use your existing log in.
You can log in to Coiled by running

```bash
coiled login
```

or by setting your Coiled API token using the ``DASK__COILED_TOKEN`` environment variable.
See https://docs.coiled.io/user_guide/setup/tokens.html for more details.

Once you have a Coiled API token set where you'll be running the worker, you can start the worker like this:

```bash
prefect worker start -p "my-coiled-pool" --type "coiled"
```

### Coiled API token specified through Prefect credentials block

Things are more complicated if you need to specify the Coiled API token to use for the work pool,
but this does give you more flexibility and allows you to change the Coiled credentials
for a work pool without restarting the worker.

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

Now, you can start a worker for this pool:

```bash
prefect worker start -p "my-coiled-pool"
```

The worker will use the credentials from the credentials block when running flows via Coiled.

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

You can use the ``region``, ``cpu``, ``memory``, and ``gpu`` job variables to control the cloud hardware that your flow will run on.
These match the arguments to the ``coiled batch run`` CLI documented at https://docs.coiled.io/user_guide/api.html#coiled-batch-run

## Run the flow

```bash
prefect deployment run 'my-flow/my-coiled-deploy'
```
