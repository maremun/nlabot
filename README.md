# NLAbot
Welcome to **NLAbot**, Telegram bot for uploading and checking coding parts of
homework via Telegram. **NLAbot** is used at [Numerical Linear Algebra](http://nla.skoltech.ru/) class,
hence the name. Check out our [Github repo](https://github.com/oseledets/nla2017).
NLA Instructors team is from [Scientific Computing group](http://oseledets.github.io/).

## Architecture Design
**NLAbot** consists of three functional parts: Bot, TA and Jail. Bot interacts
with a student, registers and uploads submissions. TA brings up a container
with the checking process (Jail). Once Jail processing is over, TA grades the
work and sends a notification. Jail acts as an isolated checker, running
student's code and testing it.

Quick launch with docker-compose in detached mode:

```bash
docker-compose build
docker-compose up -d --scale ta=4 bot ta
```

The last command scales the number of TAs. In older docker-compose use

```bash
docker-compose up -d bot ta
docker-compose scale ta=4
```
for launch and scaling.

### Bot

Bot is a primary point of contact. It handles all incoming Telegram updates,
i.e. user messages, using long polling. It registers new students by updating
database entries. To distribute and allow for asynchronous homework checking
among TAs, Bot relies on Redis Queue.

You can start bot locally like so:

```bash
nlabot serve
```

or run a container with the following commands:

```bash
docker-compose build bot
docker-compose up bot
```

### TA

NLABot has a pool of background workers called TAs. As soon as submission arrives,
it is queued for a check. The job is picked up by one of TAs from the pool. TA
runs in background and launches synchronously an isolated container (Jail) to
run a number of checks on a submitted homework solution. Once Jail finishes,
TA reads the result (see details below) and calculates the grades and updates
database entries.

Run locally:

```bash
nlabot work
```

or start a container with TA:

```bash
docker-compose build ta
docker-compose up ta
```

### Jail

Jail is a part of NLAbot responsible for isolation of students' code.
The bot process in Jail imports student's Jupyter notebook,
runs a set of tests and then tells the caller TA student's score. 

In order to check a notebook manually one can run the following NLAbot CLI
command. The command takes two positional arguments: checker identifier and
a path to the notebook.

This command demonstrates checking in a host system without any isolation:

```bash
    nlabot imprison test notebooks/testnotebook.ipynb
```

And this one uses predefined compose-file to check student notebook in
isolation:

```bash
    docker-compose build cell
    docker-compose run cell
```

#### Isolation

The key aspect is using cgroups via docker in order to limit
memory and CPU usage and to prohibit any networking (see docker-compose.yml).

#### TA-Jail communication

There is no special IPC mechanism between TA and Jail. It is pretty straight
forward and uses stdout, any shared file or FIFO.
The caller has a right to select communication resource with `--output` option.
The default value is stdout.

Communication protocol between TA and Jail is one directional from Jail to TA
and it is based on JSON formatted messages. TA is waiting for any JSON
encoded message on its side and Jail writes tests results as JSON
formatted notification.

#### Nuances

There is a couple of non-trivial bootstrapping procedures before homework
checking. 

**Importing notebooks**

Fortunately, there is a standard solution for importing Jupyter
notebooks as modules. It introduces specific module finder and module loader.

**Handling notebooks content**

Due to interactive nature of Jupyter notebooks one should restrict its
content.
Jupyter cell magic `%matplotlib inline` is ubiquitous. Meanwhile it poses a
problem as it is an infeasible clause in a non-interactive mode. This is
handled with patching matplotlib magic with a stub function and setting
matplotlib backend as 'agg'.
