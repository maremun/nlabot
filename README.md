# NLAbot
Welcome to **NLAbot**, Telegram bot for uploading and checking coding parts of homework via Telegram.
NLAbot is used at Numerical Linear Algebra class. Check out our [Github repo](https://github.com/oseledets/nla2017).
NLA Instructors team is from [Scientific Computing group](http://oseledets.github.io/).

## Architecture Design
NLA bot consists of three functional parts: Bot, TA and Jail. Bot interacts
with a student, registers and uploads submissions. TA brings up a container
with the checking process (Jail). Once Jail processing is over, TA grades the
work and sends a notification. Jail acts as an isolated checker, running
student's code and testing it.

### NLA Bot

You can start bot locally like so:

```bash
nlabot serve
```
or run a container with the following commands:

```bash
docker-compose build bot
docker-compose up bot
```

### NLA TA

Run locally:

```bash
nlabot work
```

Start a container with TA:

```bash
docker-compose build ta
docker-compose up ta
```

You can scale ny increasing the number of TAs:

```bash
docker-compose scale ta=4
```

### Jail

Jail is a part of NLAbot responsible for isolation of
students' code. The key aspect is using cgroups via docker in order to limit
memory and CPU usage and to prohibit any networking. The bot process in Jail
imports student's Jupyter notebook, runs some set of checks and then tells the
caller TA student's score. There is no special IPC mechanism between TA and
Jail. It is pretty straight forward and uses stdout or any shared file or FIFO.
The caller has a right to select communication resource with `--output` option
(see usage of `nlabot` entry). The default value is stdout. Communication
protocol between TA and Jail is one directional from Jail to TA and it is based
on JSON formatted messages. So, TA is waiting for any JSON encoded message on
its side and Jail should write checks results as JSON formatted notification.

There is a range of non-trivial bootstrapping procedures before homework
checking. The first one is notebook importing. Fortunately there is standard
solution that introduces specific module finder and module loader for Jupyter
notebooks. The second one is the most formidable since it should not restrict
content of students notebook strongly. For example, using `%matplotlib inline`
cell magic is frequent for Jupyter user, but this is unfeasible clause in a
non-interactive mode.

In order to check notebook manually one can run the following NLAbot CLI
command. The command takes two positional arguments: identifier of checker and
jupyter notebook.

This command demonstrates checking in a host system without any isolation:

```bash
    nlabot imprison test notebooks/testnotebooks.ipynb
```

And this one uses predefined compose-file to check student notebook in
 isolation:

```bash
    docker-compose build cell
    docker-compose run cell
```
