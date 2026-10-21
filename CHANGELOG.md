# Changelog

## [1.2.0](https://github.com/thekhoo/pyrail-uk/compare/v1.1.0...v1.2.0) (2026-10-21)


### Features

* add HistoricServiceClient.find_journeys ([bb7a123](https://github.com/thekhoo/pyrail-uk/commit/bb7a12316a589c45b2bad8a1d152011a34cb9443))
* add HistoricServiceClient.find_journeys and a shared request client ([2f2eb39](https://github.com/thekhoo/pyrail-uk/commit/2f2eb39301f13d4dca7b486b280c4269b22dc0f9))
* add shared BaseRequestClient that retries 429 and 5xx ([7900f73](https://github.com/thekhoo/pyrail-uk/commit/7900f7316f5992715c8ebd7547cd082a2fa04ed3))


### Bug Fixes

* satisfy pyrefly in the request client tests ([0b27b6d](https://github.com/thekhoo/pyrail-uk/commit/0b27b6d963478af67f3103f893ef6cebd6247859))


### Documentation

* document find_journeys and the shared request client ([096a8df](https://github.com/thekhoo/pyrail-uk/commit/096a8df9a4e18a0b38252644d5ca97b4de55ecc1))
* use the real TrainService field name in the departures example ([2cd2585](https://github.com/thekhoo/pyrail-uk/commit/2cd2585acea711ef65892e1d81fb6446e79d0f5f))
* write a usage guide for all clients ([33f7290](https://github.com/thekhoo/pyrail-uk/commit/33f72909261f8b8394965e478b540b1c2b3508a8))

## [1.1.0](https://github.com/thekhoo/pyrail-uk/compare/v1.0.4...v1.1.0) (2026-10-20)


### Features

* **api:** add default retry strategy and timeout to API clients ([0280d31](https://github.com/thekhoo/pyrail-uk/commit/0280d31e62d7706798a5f85736bca88dbc052b31))
* **historic:** validate HSP responses with pydantic ([37545e4](https://github.com/thekhoo/pyrail-uk/commit/37545e48cbec6ceec5208e14afc6e8e677527200))
* **historic:** validate HSP responses with pydantic models ([4ca4c40](https://github.com/thekhoo/pyrail-uk/commit/4ca4c40c0468938f25669104495f4f877ffe41cd))


### Documentation

* describe the split release workflows ([c1401e7](https://github.com/thekhoo/pyrail-uk/commit/c1401e74f4fa4d11e878f05c837085ea288de8ab))
* document historic service responses ([06453b4](https://github.com/thekhoo/pyrail-uk/commit/06453b4f02de77596c105bf37338b4e102a2c1fb))
* document the release-please flow ([f73434b](https://github.com/thekhoo/pyrail-uk/commit/f73434b897d3003e6e71fcfe3e8ca85037a7f1be))
