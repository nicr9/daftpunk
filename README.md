# Daftpunk

A website for tracking and analysing the property market by scraping details from [daft.ie](http://www.daft.ie).

## Rewrite

**N.B.** I'm currently embarking on a complete rewrite of daftpunk!

Both the old and new projects are currently visible within this branch so to
clarify, the following paths describe files relating to the old project:

* daftpunk/\*
* frontend/\*

Everything else represents the bleeding edge version of the project.

The reason for the rewrite is so I can take a whole new approach to the
architecture and apply a lot of what I've learned about web scraping to achieve
a much cleaner and more generally useful project.

## Installing the dp2 Module

If you're hoping to develop against the dp2 python module or submit patches to daftpunk, you'll need [python2.7](https://www.python.org/downloads/release/python-279/), [setuptools](https://pypi.python.org/pypi/setuptools) and [pip](https://pip.pypa.io/en/stable/installing/)!

Finally, to install dp2:

```bash
make install
```

## Development Environment

The development environment uses docker-compose to deploy daftpunk locally.

You should assume that this mode is unsuitable for a production environment, for that see [Production deployment](#production-deployment) below.

### Setup

For help getting docker and docker-compose installed [checkout this page.](https://docs.docker.com/compose/install/)

### Build

This step is optional. You only need to do it if you're a developer working on daftpunk.

If you're working on `dp2`, you'll need to rebuild everything:

```bash
make base-build dev-build
```

If you're working on the web app of anything in `scripts/` you just need to:

```bash
make dev-build
```

### Deploy

To deploy daftpunk locally:

```bash
make dev-up dev-post-up
```

This starts up the postgres, redis and a web frontend as linked containers. It also initialises inportant info in the cache.

And to open the web app in Chrome:

```bash
make dev-open
```

When you've created an account and subscribed to a few regions, you'll need the backend process to scrape the details for properties in your subscribed regions:

```bash
make dev-backend
```

You'll need to trigger this backend process everytime you want updated info.

### Teardown

To tear down the development environment:

```bash
make dev-down
```

## Production Deployment

The production environment uses [Kubernetes](https://kubernetes.io/) to deploy daftpunk. This can be locally using [Minikube](https://github.com/kubernetes/minikube) or to a server/cloud environment that has been set up using one of the [countless systems availabe](https://kubernetes.io/docs/getting-started-guides/).

Daftpunk requires Kubernetes version 1.4+.

### Setup

Once you've set up a Kubernetes cluster and installed `kubectl` using the [guide in the docs](https://kubernetes.io/docs/user-guide/prereqs/) you should be good to deploy!

If you'd like to build/develop daftpunk locally, you'll also need [Docker](https://docs.docker.com/engine/installation/linux/) installed.

### Build

This step is optional. You only need to do it if you're a developer working on daftpunk.

If you're makind changes to `dp2`, you'll need to rebuild everything:

```bash
make base-build web-rebuild scripts-rebuild
```

If you're just making changes to the web app:

```bash
make web-build
```

Or just one/more of the scripts (`cache.py`, `backend.py`, etc.):

```bash
make scripts-build
```

### Deploy

Deploying to Kubernetes is simple:

```bash
make prod-up
```

This will deploy everything (including restoring info in cache and scheduling the backend script to scrape property info every night at 12:00).

### Teardown

To tear down the production environment:

```bash
make prod-down
```

## Author

```
Name: Nic Roland<br>
Email: nicroland9@gmail.com<br>
Twitter: @nicr9_
```

## Contributors

* [Peter Keogh](https://github.com/keoghpe)
* [Kingsley Kelly](https://github.com/KingsleyKelly)
* [Brian Duffy](https://github.com/bmduffy)
