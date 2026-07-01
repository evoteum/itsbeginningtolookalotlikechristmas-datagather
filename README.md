[//]: # (STANDARD README)
[//]: # (https://github.com/RichardLitt/standard-readme)
[//]: # (----------------------------------------------)
[//]: # (Uncomment optional sections as required)
[//]: # (----------------------------------------------)
[//]: # (AI INSTRUCTIONS)
[//]: # (Hello friendly AI agent! Please do your best to comply with)
[//]: # (the following style guide in this document.)
[//]: # (> Comments)
[//]: # (All [//]: # comment lines in this file are part of)
[//]: # (the Standard README template structure. Preserve them exactly!)
[//]: # (Do not remove, reword, merge, or move them when editing content.)
[//]: # (This includes comments inside sections that already have content.)
[//]: # (> Line length)
[//]: # (Keep all prose lines to a maximum of 88 characters. Exclude tables)
[//]: # (and fenced code blocks from this limit.)
[//]: # (----------------------------------------------)



[//]: # (Title)
[//]: # (Match repository name)
[//]: # (REQUIRED)

# itsbeginningtolookalotlikechristmas-datagather

[//]: # (Banner)
[//]: # (OPTIONAL)
[//]: # (Must not have its own title)
[//]: # (Must link to local image in current repository)



[//]: # (Badges)
[//]: # (OPTIONAL)
[//]: # (Must not have its own title)



[//]: # (Short description)
[//]: # (REQUIRED)
[//]: # (An overview of the intentions of this repo)
[//]: # (Must not have its own title)
[//]: # (Must be less than 120 characters)
[//]: # (Must match GitHub's description)

Gathers the data for ItsBeginningToLookALotLike.Christmas

[//]: # (Long Description)
[//]: # (OPTIONAL)
[//]: # (Must not have its own title)
[//]: # (A detailed description of the repo)

Fetches the daily popularity score for Perry Como's
[It's Beginning to Look a Lot Like Christmas](https://youtu.be/KmddeUJJEuU) from the
[Deezer API](https://developers.deezer.com/api) and appends it to `data.csv` in the
[itsbeginningtolookalotlikechristmas](https://github.com/evoteum/itsbeginningtolookalotlikechristmas)
repository. That commit triggers a site image rebuild, keeping
[ItsBeginningToLookALotLike.Christmas](https://ItsBeginningToLookALotLike.Christmas) up to date.

A `CronJob` running in the [kubernetes-lab-services](https://github.com/evoteum/kubernetes-lab-services)
cluster (Helm chart in [`chart/`](chart/)) runs a pre-built image of `python/main.py` daily.

Previously this used the Spotify Web API, but Spotify began requiring a paid Premium subscription
to access their API, making it no longer viable for this use case.



## Table of Contents

[//]: # (REQUIRED)
[//]: # (Managed automatically)
[//]: # (Changes between TABLE_OF_CONTENTS_START and TABLE_OF_CONTENTS_END)
[//]: # (markers will be overwritten)
[//]: # (Set `tocgen: true` in estate-repos/repos.yaml)
[//]: # (to enable automatic table of contents management.)
[//]: # (Or just do it manually like a weirdo, you do you...)

[//]: # (TOCGEN_TABLE_OF_CONTENTS_START)

- [Install](#install)
- [Usage](#usage)
- [Secrets](#secrets)
- [Documentation](#documentation)
- [Repository Configuration](#repository-configuration)
- [Contributing](#contributing)
- [License](#license)
    - [Code](#code)
    - [Non-code content](#non-code-content)

[//]: # (TOCGEN_TABLE_OF_CONTENTS_END)

[//]: # (## Security)
[//]: # (OPTIONAL)
[//]: # (May go here if it is important to highlight security concerns.)



[//]: # (## Background)
[//]: # (OPTIONAL)
[//]: # (Explain the motivation and abstract dependencies for this repo)



## Install

[//]: # (Explain how to install the thing.)
[//]: # (OPTIONAL IF documentation repo)
[//]: # (ELSE REQUIRED)

Install the Python requirements:

```shell
pip install -r python/requirements.txt
```

Set the required environment variables (see [Secrets](#secrets)), then run:

```shell
python python/main.py
```

If `site/data.csv` is not found, the script will clone
[itsbeginningtolookalotlikechristmas](https://github.com/evoteum/itsbeginningtolookalotlikechristmas)
into the current directory automatically.

## Usage
[//]: # (REQUIRED)
[//]: # (Explain what the thing does. Use screenshots and/or videos.)

In production, the `CronJob` runs automatically at midnight UTC daily. To trigger it
manually, use `kubectl create job` from the CronJob in the
`itsbeginningtolookalotlikechristmas-datagather` namespace.



[//]: # (Extra sections)
[//]: # (OPTIONAL)
[//]: # (This should not be called "Extra Sections".)
[//]: # (This is a space for ≥0 sections to be included,)
[//]: # (each of which must have their own titles.)

## Secrets

Sourced from OpenBao via the `openbao` `ClusterSecretStore` in the cluster.
For local development, set these as environment variables.

| OpenBao path          | Key              | Value                            |
|-----------------------|------------------|----------------------------------|
| `platform/evoteumbot` | `app_id`         | GitHub App ID                    |
| `platform/evoteumbot` | `ssh_privatekey` | GitHub App private key (RSA PEM) |

The Deezer API requires no authentication.

## Documentation

Further documentation is in the [`docs`](docs/) directory.

## Repository Configuration

> [!WARNING]
> This repo is controlled by OpenTofu in the [estate-repos](https://github.com/evoteum/estate-repos) repository.
>
> Manual configuration changes will be overwritten the next time OpenTofu runs.

[//]: # (## Requirements)
[//]: # (OPTIONAL)
[//]: # (List runtime and toolchain prerequisites with minimum versions.)



[//]: # (## API)
[//]: # (OPTIONAL)
[//]: # (Describe exported functions and objects)



[//]: # (## Maintainers)
[//]: # (OPTIONAL)
[//]: # (List maintainers for this repository)
[//]: # (along with one way of contacting them - GitHub link or email.)



[//]: # (## Thanks)
[//]: # (OPTIONAL)
[//]: # (State anyone or anything that significantly)
[//]: # (helped with the development of this project)



## Contributing
[//]: # (REQUIRED)
If you need any help, please log an issue and one of our team will get back to you.

PRs are welcome.


## License
[//]: # (REQUIRED)

### Code

All source code in this repository is licenced under the GNU Affero General Public
License v3.0
[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.en.html).
A copy of this is provided in the [LICENSE](LICENSE).

### Non-code content

All non-code content in this repository, including but not limited to images, diagrams
or prose documentation, is licenced under the Creative Commons Attribution-ShareAlike
4.0 International licence,
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
