# redditripper
Downloads all images of the subreddits specified in a text file 

## Usage
### Command Line
```
You can use it without arguments as following:
python3 redditripper.py

When you use the --help or -h argument you will
get a help text I will paste it below:

usage: redditripper.py [-h] [--verbose] [-f SUBREDDIT_FILE] [-c CATEGORY]
                       [-l LIMIT]

optional arguments:
  -h, --help            show this help message and exit
  --verbose             Print verbose status messages
  -f SUBREDDIT_FILE, --subreddit_file SUBREDDIT_FILE
                        The file in which the subreddits are stored
  -c CATEGORY, --category CATEGORY
                        The category, can be hot, top and new
  -l LIMIT, --limit LIMIT
                        The amount of posts you want to fetch per subreddit.
                        Can be from 1 to 100.
```

### As Library
```PYTHON
# Initiate the RedditRipper class
'''
This will just call the __init__ method.

Args:
    All args are optional.
    
    is_verbose: is a boolean to check if verbose status messages                 should be printed. The default value is False.
    subreddit_file: the file where the subreddits are stored. The                    default value is 'subreddits.txt'
    category: the category, can be 'hot', 'top' and new.
    limit: the amount of posts you want to fetch per subreddit.

Returns:
    The instance of the RedditRipper class
'''
reddit_ripper = RedditRipper()

# Run the default method to just
# fetch the data and download the images
reddit_ripper.run()

# For further explanation read the docstrings 
# in the 'redditripper.py' file.
```

## Dependencies
* requests
* bs4