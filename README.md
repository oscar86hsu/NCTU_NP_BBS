# NCTU_NP_BBS
Bulletin Board System (BBS).
<br>
The program handles multiple connections and receives user command from standard input.

---

## Requirement
- Python 3.6 or above

## User Commands
| Command Format | Description|
| ------------- | -------------|
| register {username} {email} {password} | Register with username, email and password. {username} must be unique. {email} and {password} have no limitation.<br>If username is already used, show failed message, otherwise it is success. |
| login {username} {password} | Login with username and password.<br>Fail(1): User already login.<br>Fail(2): Username or password is incorrect. |
| logout | Logout account.<br>If login not yet, show failed message, otherwise logout successfully. |
| whoami | Show your username.<br>If login not yet, show failed message, otherwise show username. |
| exit | Close connection. |

<br>

## Usage
- Server : Use ./server {PORT} to run the server with specific port. Default port is 3000.

- Client : Use telnet to connect the server and input command.


