# Fawkes:

## Requirements:

- Ubuntu 16.04 or lower
    We are relying on Mahimahi to record and replay web pages. Since Mahimahi binaries are compiled for ubuntu 16.04 or lower versions, we also require a compatible OS.
    The following instructions are tested on Ubuntu 16.04.

- Follow the instructions in [TreeMatching](https://github.com/fawkes-nsdi20/TreeMatching) submodule in order to install all the required dependencies for it.

- Install other dependencies:
    ```
    $ sudo apt install nodejs-legacy
    $ sudo apt-get install build-essential libssl-dev
    ```

## Setup Enviroment:
- Download this [Chrome binary](https://drive.google.com/file/d/1BdwTTwh_TD7hDhrot2YaJe1YhvZj9g6W/view?usp=sharing) which fixes an SSL issue for correct replay of warm cache scenarios:
- Unzip the downloaded file and place it under *mm-recording*:
    ```
    $ unzip mm-recording/chrome-caching.zip -d mm-recording/
    ```

- From the root directory run the following:
    ```
    $ npm install
    ```

## Yahoo homepage Example:
Out of Alexa 500 pages dataset, we have taken www.yahoo.com as an example here. The files related to this example are under *examples/yahoo*.
Two different versions of the same web page (www.yahoo.com) is recorded 12 hours apart, using Mahimahi.
The output of mahimahi recordings at time 0 (initial) and 12-hours later (target) are stored under *record/v0*, *record/v1* directories, respectively.
These two mahimahi recordings are used as input arguments to Fawkes.

To simulate how Fawkes runs, we create a mahimahi directory (stored under *replay/fawkes*) which contains both Fawkes static template and dynamic patch.
In order to have a fair comparison, we also create another mahimahi directory which is an almost-copy of target directory. The only difference is that we have updated the headers of all cacheable files to be cacheable for one year. This copy is stored under *replay/default*.

In order to create the fawkes and default directories, run the following command:
```$ ./fawkes-example.sh```

When *replay/fawkes* is replayed using Mahimahi replay tool, Fawkes static template is served instead of the default top level HTML. Fawkes static template includes a JS patcher library which requests the dynamic patch from backend. Once the dynamic patch is received (served as a part of mahimahi directory), the JS patcher applies it on the static template to create the final state of the page. To see the visual results, run:
```$ ./replay.sh examples/yahoo/replay/fawkes```

In order to compare it with the default response (target):
```$ ./replay examples/yahoo/replay/default```

