# Robot test suit

In CI we are using [robot test framework](https://robotframework.org/) to test certain functionalities of the core network functions. 

To execute robot test you would need to install the prerequisite. 

```bash
# you can create a virtual environment and install in that environment
pip install -r requirements.txt
sudo apt install tshark
```

Mention the image tags in `image_tags.py`. Some images are not published. 

To execute robot test you would need: 

```bash
# to list the tests which will run 
robot --dryrun test
robot --outputdir archives test
```

