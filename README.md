# Auth

Auth microservice integrated with [kong](https://github.com/Kong/kong) for registration and issuing tokens.

## Features

- White-listed email registration
- Anonymous: RSA encrypted personal information(email) and random identity
- issue and revoke JWT tokens

## Deploy

This project continuously integrates with docker. Go check it out if you don't have docker locally installed.

```shell
docker run -d -p 8000:8000 shi2002/auth
```

Configurations:

| Key                             | Example Value                                | Description                                                  |
| ------------------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| SANIC_MODE                      | dev                                          | 'production' in production mode, otherwise in dev mode       |
| SANIC_DB_URL                    | mysql://username:pwd@host:port/db | required                                                     |
| SANIC_KONG_URL                  | http://kong:8001                             | kong admin api, required                                     |
| SANIC_KONG_TOKEN                | token                                        | set "Authorization" key auth in kong to secure admin api     |
| SANIC_EMAIL_WHITELIST           | ["example.com", "example.org"]               | domains allowed to register, default to [], accepting all domains |
| SANIC_VERIFICATION_CODE_EXPIRES | 10                                           | verification code expires in minutes                         |
| SANIC_EMAIL_HOST                | smtpdm.aliyun.com                            | smtp email service                                           |
| SANIC_EMAIL_PORT                | 465                                          |                                                              |
| SANIC_EMAIL_USER                | no-reply@example.com                         |                                                              |
| SANIC_EMAIL_PASSWORD            | password                                     |                                                              |

## Usage

API Docs are available at /docs

## Badge

[![build](https://github.com/OpenTreeHole/auth/actions/workflows/master.yaml/badge.svg)](https://github.com/OpenTreeHole/auth/actions/workflows/master.yaml)
[![dev build](https://github.com/OpenTreeHole/auth/actions/workflows/dev.yaml/badge.svg)](https://github.com/OpenTreeHole/auth/actions/workflows/dev.yaml)

[![stars](https://img.shields.io/github/stars/OpenTreeHole/auth)](https://github.com/OpenTreeHole/auth/stargazers)
[![issues](https://img.shields.io/github/issues/OpenTreeHole/auth)](https://github.com/OpenTreeHole/auth/issues)
[![pull requests](https://img.shields.io/github/issues-pr/OpenTreeHole/auth)](https://github.com/OpenTreeHole/auth/pulls)

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

### Powered by

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

## Contributing

Feel free to dive in! [Open an issue](https://github.com/OpenTreeHole/auth/issues/new) or submit PRs.

### Contributors

This project exists thanks to all the people who contribute.

<a href="https://github.com/OpenTreeHole/auth/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=OpenTreeHole/auth" />
</a>

## Licence

[![license](https://img.shields.io/github/license/OpenTreeHole/auth)](https://github.com/OpenTreeHole/auth/blob/master/LICENSE)
© OpenTreeHole