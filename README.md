## GabLeaks-Analysis

This codebase relates to the [GabLeaks release](https://ddosecrets.com/wiki/GabLeaks) from Distributed Denial of Secrets. While the Gab data itself is limited distribution, this helper code is public.

The original release format is a Postgresql database dump that includes data in three tables: accounts, statuses, and verifications. However, both the 'statuses' and 'accounts' tables contain a 'data' column where most of the relevant details are stored in JSON.

The mixed JSON / SQL format is not the most convenient for analysis. This script expands the data, creating new `statuses_expanded` and `accounts_expanded` tables with individual typed fields instead of one big JSON blob. The schemas are as follows:

**statuses\_expanded**

| Field                      | Type                     |
| -------------------------- | ------------------------ |
| id                         | bigint                   |
| bookmark\_collection\_id   | bigint                   |
| card                       | jsonb                    |
| content                    | text                     |
| created\_at                | timestamp with time zone |
| emojis                     | jsonb                    |
| expires\_at                | timestamp with time zone |
| favourited                 | boolean                  |
| favourites\_count          | bigint                   |
| group\_                    | jsonb                    |
| has\_quote                 | boolean                  |
| in\_reply\_to\_account\_id | bigint                   |
| in\_reply\_to\_id          | bigint                   |
| language                   | text                     |
| media\_attachments         | jsonb                    |
| mentions                   | jsonb                    |
| pinnable                   | boolean                  |
| pinnable\_by\_group        | boolean                  |
| plain\_markdown            | text                     |
| poll                       | jsonb                    |
| quote                      | jsonb                    |
| quote\_of\_id              | bigint                   |
| reblog                     | jsonb                    |
| reblogged                  | boolean                  |
| reblogs\_count             | bigint                   |
| replies\_count             | bigint                   |
| revised\_at                | text                     |
| rich\_content              | text                     |
| sensitive                  | boolean                  |
| spoiler\_text              | text                     |
| tags                       | jsonb                    |
| url                        | text                     |
| visibility                 | text                     |

**accounts\_expanded**

| Field                      | Type                     |
| -------------------------- | ------------------------ |
| id                         | bigint                   |
| email                      | text                     |
| password                   | text                     |
| name                       | text                     |
| bot                        | boolean                  |
| url                        | text                     |
| note                       | text                     |
| avatar                     | text                     |
| emojis                     | jsonb                    |
| fields                     | jsonb                    |
| header                     | text                     |
| is\_pro                    | boolean                  |
| locked                     | boolean                  |
| is\_donor                  | boolean                  |
| created                    | timestamp with time zone |
| is\_investor               | boolean                  |
| is\_verified               | boolean                  |
| display\_name              | text                     |
| avatar\_static             | text                     |
| header\_static             | text                     |
| statuses\_count            | bigint                   |
| followers\_count           | bigint                   |
| following\_count           | bigint                   |
| is\_flagged\_as\_spam      | boolean                  |

### Usage

First, ensure you already have the dataset loaded into Postgresql. Installing and configuring postgres, creating a database and user, and importing the database contents from a SQL dump, are out of scope for this README.

Second, install dependencies for this project:

    pip3 install -r requirements.txt

Or install manually with:

    pip3 install psycopg2 tqdm

Finally, launch the script like:

    ./expand.py <sql_host> <sql_user> <sql_db_name>

For example:

    ./expand.py localhost postgres gableaks

You'll be prompted for your postgres user's password, and then the script should take care of everything from there. There's a progress bar included - since there are about 39 million statuses, expanding the table took a little over two hours during development tests.
