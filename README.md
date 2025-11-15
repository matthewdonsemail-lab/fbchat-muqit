<div align="center">

# fbchat-muqit Facebook & Messenger API

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fbchat-muqit)
[![fbchat-muqit](https://badgen.net/pypi/v/fbchat-muqit/)](https://pypi.org/project/fbchat-muqit/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**fbchat-muqit** An Unofficial Asynchronous Facebook Messenger API designed to interact with Facebook and Messenger. As It is an Unofficial API we are not responsible if you get banned by Facebook. We recommend to use a dummy Facebook account. For more details check the [Documentation](http://fbchat-muqit.rtfd.io/).
</div>

> [!Note]
> Bumped from version `1.1.31` to `1.2.0` and version `1.2.0` is a rewrite version meaning the library has been fully rewritten and Major changes has been made. The API is now fully Documented and the usage examples are updated.  

> [!WARNING]
> Due to `end-to-end` encryption sending messages to other Users is not supported anymore. You can send messages to Group Chat, Room Chat and to pages. [See more](https://about.fb.com/news/2024/03/end-to-end-encryption-on-messenger-explained/)
> You may still be able to send messages to another User if the that User account is inactive for many years because `end-to-end` encryption is not applied when sending message to those account unless the account is Opened again. 


## 🛠️ Installation

You can install fbchat-muqit using pip:

```bash
pip install fbchat-muqit

```

For the latest development version:

```bash
pip install git+https://github.com/togashigreat/fbchat-muqit.git 

```


## 📙 Documentation

The API is Documented. [Read The Documentation](http://fbchat-muqit.rtfd.io/). 


## 🔧 Prerequisites

- Python 3.9+
- A Facebook account (It's safer to use old unused account)
- Facebook account cookies 🍪


## 📖 Usage Example

To login in Facebook you will need Facebook account cookies. Since login via email and password is no longer supported. 

To get your Facebook account cookies. First login in your Facebook account and then add [C3C Chrome extension](https://github.com/c3cbot/c3c-ufc-utility) in your browser. Open a your Facebook account in a browser tab and use this extension to get your account cookies. Copy the cookies and save them in a json file. We will use the cookies to interact with Facebook server. We will call this account `Client` account.



A basic example of How to use it.

```python
from fbchat_muqit import Client, Message, EventType

client = Client(cookies_file_path="cookies.json")

@client.event
async def on_message(message: Message):
    # To avoid spam check if sender_id is client's id or not
    if message.sender_id != client.uid:
        # echo the message
        await client.send_message(message.text, message.thread_id)

client.run()

```

Save the code in file `test.py` and now run the code.

```bash
python3 test.py
```

If It logins succesfully then Use another Facebook account to create a messenger group and add both of the accounts to the group. Now, send message to the group and fbchat_muqit Client account will listen to all incoming messages and events. If everything works properly It should reply and react to the message sent by your other account with an emoji. 


### 📄 License

This project is distributed under a dual-license model:

- **BSD-3-Clause License**: Parts of the code are reused and adapted from the original [fbchat](https://github.com/fbchat-dev/fbchat) library, licensed under the BSD-3-Clause License. 
  See [LICENSE-BSD](./LICENSE-BSD.md) for details.

- **GPL v3 License**: New contributions and modifications by Muhammad MuQiT/togashigreat are licensed under the GPL v3.0 License.
See [LICENSE](./LICENSE.md) for details.

### ✉️Contact Me 

- [Facebook](https://facebook.com/muqit.dev)

## 🚀 HTTP API service

Alongside the Python package, the repository now bundles a thin FastAPI wrapper
that exposes fbchat-muqit through a deployable HTTP interface. The service keeps
the original library API intact while offering:

- `POST /groups/scrape` and `POST /groups/scrape/run` – run-once scrape
  operations that accept a payload inspired by Apify's Facebook group scraper
  schema (cookies, groupUrl, count, cursor, sortType, scrapeUntil, min/max
  delay, proxy, etc.).
- `GET /openapi.json`, `GET /docs`, and `GET /redoc` – discoverable OpenAPI 3
  schema with interactive Swagger UI.
- `GET /healthz` – lightweight liveness probe for deployment platforms.

### Authentication

The API can read Facebook cookies from two sources:

1. `cookie` array in the request body – highest precedence and only used for
   that request.
2. `FB_COOKIES_FILE_PATH` environment variable – fallback path to a JSON file
   mounted inside the container.

If both are available, the in-request cookies win for that call, mirroring the
behaviour of the original library.

### Running locally

Install the optional `api` dependencies and launch the ASGI app:

```bash
pip install .[api]
uvicorn fbchat_muqit_api.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs to test the endpoints.

### Docker & Railway deployment

- Build locally: `docker build -t fbchat-muqit-api .`
- Run: `docker run -p 8000:8000 -e FB_COOKIES_FILE_PATH=/run/secrets/cookies.json \
    -v $(pwd)/cookies.json:/run/secrets/cookies.json fbchat-muqit-api`
- Railway: deploy the repository as-is – the provided `Dockerfile`, `Procfile`
  and `railway.json` configure a single web service that binds to
  `0.0.0.0:$PORT`.

Environment variables:

| Name | Description |
| --- | --- |
| `FB_COOKIES_FILE_PATH` | Optional absolute path to `cookies.json` inside the container. |
| `FB_DEFAULT_MIN_DELAY` | Default minimum delay (seconds) between pagination requests. |
| `FB_DEFAULT_MAX_DELAY` | Default maximum delay (seconds) between pagination requests. |
| `FB_LOG_LEVEL` | Log level propagated to fbchat-muqit `Client` instances. |

