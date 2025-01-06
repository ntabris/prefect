# `prefect-coiled`

Prefect worker for running flows on Coiled.

## Installation

To start using `prefect-coiled`:

```bash
pip install prefect-coiled  # or `pip -e .` install from source 
prefect worker start -p "my-coiled-pool" --type "coiled"
```

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

And run the flow:

```bash
prefect deployment run 'my-flow/my-coiled-deploy'
```
