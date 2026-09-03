# Python Buffers stdout When Redirected

Writing to a redirected file is block-buffered, so a running script's output can look empty until the process exits. Capture logs with `python -u` to flush immediately. This bit us during verification: the log appeared 0 bytes while the script was mid-run.
