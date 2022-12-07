# Python async client/server using json instant messaging
gb: client-server applications course

## Stack:
  - asyncio (server / client-in)
  - threading (client-out)
  - unittest
  - Sqlalchemy
  - aiosqlite

## Description of the project:
Async server with async client using threading for input stream;

Both client and server have optional start parameters:

-a --addr for address;

-p --port for port;

Default parameters can be set in ./project/utils/configs.py file at HOST, PORT constants.

Project uses default http codes to interact.

### Logging
I used default python library logging to implement this feature. So nothing special here. There are two types of loggers for client actions and server actions, 
created by logger factory class. Logger level can also be set in ./project/utils/configs.py.

** HERE WILL BE GIF **

** HERE WILL BE EXAMPLE OF THE INTERACTION **
