recipe-scraper

Compile recipes from your your favourite webpages!

1. Create a virtual environment
`$ python -m venv env`
2. Activate virtual environment
`$ source env/bin/activate`
3. Install all dependencies
`$ python -m pip install -r requirements.txt`
4. Run the script $ python main.py
`$ python main.py`

How it works:
- The script asks for an with an entry point URL to start at.
- The script recursively traverses through hyperlinks and compiles a list of URLs that are within the same parent domain.
- The script performs some sanity checks to see if the webpage contains a recipe and, if so, compiles them in `crawled_recipes.md` for user. This is repeated until `n` recipes have been compiled.
- Upon re-run, `main.py` will take a look at URLs that it has not yet visited and continue searching for a new set of `n` recipes that will be added to `crawled_recipes.md`.

Tips:
- Start with an entry point URL that you like. Here are some options you can consider:
    - [Food Reference]("https://www.foodreference.com/")
    - [Sally's Baking Addiction]("https://sallysbakingaddiction.com/")
    - [New York Times Cooking]("https://cooking.nytimes.com/")
    - [Gimme Some Oven]("https://www.gimmesomeoven.com/")