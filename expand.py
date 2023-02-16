#!/usr/bin/env python3
import sys, getpass, psycopg2
from psycopg2.extras import execute_values
from collections import defaultdict
from tqdm import tqdm
import json

"""
	This script loads json blobs from the `statuses` table in the Gab table,
	parses them, and puts them in a `statuses_expanded` table with separate
	table fields for most attributes. Should make the data much easier to search
	through!
"""

SCHEMA_STATUSES = """CREATE TABLE IF NOT EXISTS statuses_expanded(
	id BIGINT PRIMARY KEY,
	bookmark_collection_id BIGINT,
	card JSONB,
	content TEXT,
	created_at timestamp with time zone,
	emojis JSONB,
	expires_at timestamp with time zone,
	favourited BOOLEAN,
	favourites_count BIGINT,
	group_ JSONB,
	has_quote BOOLEAN,
	in_reply_to_account_id BIGINT,
	in_reply_to_id BIGINT,
	language TEXT,
	media_attachments JSONB,
	mentions JSONB,
	pinnable BOOLEAN,
	pinnable_by_group BOOLEAN,
	plain_markdown TEXT,
	poll JSONB,
	quote JSONB,
	quote_of_id BIGINT,
	reblog JSONB,
	reblogged BOOLEAN,
	reblogs_count BIGINT,
	replies_count BIGINT,
	revised_at TEXT,
	rich_content TEXT,
	sensitive BOOLEAN,
	spoiler_text TEXT,
	tags JSONB,
	url TEXT,
	visibility TEXT
)"""

SCHEMA_ACCOUNTS = """CREATE TABLE accounts_expanded(
	id BIGINT PRIMARY KEY,
	email TEXT,
	password TEXT,
	name TEXT,
	bot BOOLEAN,
	url TEXT,
	note TEXT,
	avatar TEXT,
	emojis JSONB,
	fields JSONB,
	header TEXT,
	is_pro BOOLEAN,
	locked BOOLEAN,
	is_donor BOOLEAN,
	created TIMESTAMP WITH TIMEZONE,
	is_investor BOOLEAN,
	is_verified BOOLEAN,
	display_name TEXT,
	avatar_static TEXT,
	header_static TEXT,
	statuses_count BIGINT,
	followers_count BIGINT,
	following_count BIGINT,
	is_flagged_as_spam BOOLEAN
)"""

# There are ~39 million statuses - loading them all at once will exhaust all
# memory quickly, so we'll load, parse, and save 10K at a time 
CHUNK_SIZE = 10000
INSERT_STATUS = "INSERT INTO statuses_expanded VALUES %s"
INSERT_ACCOUNT = "INSERT INTO accounts_expanded VALUES %s"

# Dump object as json, *but* return None instead of 'null' so SQL won't
# think it's a string
def js(blob):
	if( blob ):
		return json.dumps(blob)
	else:
		return None

if __name__ == "__main__":
	if( len(sys.argv) != 4 ):
		sys.stderr.write("USAGE: %s <sql_host> <sql_user> <sql_db_name>\n" % sys.argv[0])
		sys.stderr.write("  For example: %s localhost postgres gab\n" % sys.argv[0])
		sys.exit(1)

	(_,dbhost,dbuser,dbname) = sys.argv
	dbpass = getpass.getpass(prompt="SQL password for user '%s': " % dbuser)
	connect_str = "dbname='%s' user='%s' host='%s' password='%s'" % (dbname,dbuser,dbhost,dbpass)
	conn = psycopg2.connect(connect_str)

	"""
	Ordinarily, cursors are implemented client-side. When you make a query,
	all results are immediately returned to the client (this Python script),
	and fetchall(), fetchmany(), and fetchone() all load from the local cache.
	Since we've got to query 39 million rows, we can't do that. Instead, we'll
	use a server-side cursor to ask Postgresql to do the caching for us.
	"""
	wc = conn.cursor() # Write cursor is client-side
	rc = conn.cursor('server_side_read_gab') # Read cursor is server-side

	# Create the new tables
	wc.execute(SCHEMA_STATUSES)
	wc.execute(SCHEMA_ACCOUNTS)

	# If you have changed the number of statuses then the loading bar will
	# have the wrong upper-bound, but that just means it'll finish before 100%
	# - the import should still run fine
	total_statuses = 39229509
	pbar = tqdm(total=total_statuses, desc="Expanding status messages")

	# While there's unparsed data left, load a chunk, parse it, write it back
	rc.execute("SELECT id,data FROM statuses")
	while( True ):
		rows = rc.fetchmany(CHUNK_SIZE)
		if( len(rows) == 0 ):
			break
		toWrite = []
		for data in rows:
			id_ = data[0]
			s = defaultdict(lambda: None, data[1])
			# List fields in correct order, and convert json blobs back to
			# strings
			thisrow = [id_, s["bookmark_collection_id"], js(s["card"]), s["content"], s["created_at"], js(s["emojis"]), s["expires_at"], s["favourited"], s["favourites_count"], js(s["group"]), s["has_quote"], s["in_reply_to_account_id"], s["in_reply_to_id"], s["language"], js(s["media_attachments"]), js(s["mentions"]), s["pinnable"], s["pinnable_by_group"], s["plain_markdown"], js(s["poll"]), js(s["quote"]), s["quote_of_id"], js(s["reblog"]), s["reblogged"], s["reblogs_count"], s["replies_count"], s["revised_at"], s["rich_content"], s["sensitive"], s["spoiler_text"], js(s["tags"]), s["url"], s["visibility"]]
			toWrite.append(thisrow)
		execute_values(wc, INSERT_STATUS, toWrite)
		pbar.update(len(rows))
	pbar.close()
	conn.commit() # Save our cached changes!!
	print("Done expanding statuses.")

	# Reset the server-side cursor now that we've committed
	rc = conn.cursor('server_side_read_gab') # Read cursor is server-side
	total_accounts = 4117381
	pbar = tqdm(total=total_accounts, desc="Expanding account list")
	rc.execute("SELECT id,email,password,name,data FROM accounts")
	while( True ):
		rows = rc.fetchmany(CHUNK_SIZE)
		if( len(rows) == 0 ):
			break
		toWrite = []
		for data in rows:
			(id_, email, password, name) = data[0:4]
			if( data[4] ):
				s = defaultdict(lambda: None, data[4])
				thisrow = [id_, email, password, name, s["bot"], s["url"], s["note"], s["avatar"], js(s["emojis"]), js(s["fields"]), s["header"], s["is_pro"], s["locked"], s["is_donor"], s["created"], s["is_investor"], s["is_verified"], s["display_name"], s["avatar_static"], s["header_static"], s["statuses_count"], s["followers_count"], s["following_count"], s["is_flagged_as_spam"]]
			else:
				thisrow = [id_, email, password, name] + [None]*20
			toWrite.append(thisrow)
		execute_values(wc, INSERT_ACCOUNT, toWrite)
		pbar.update(len(rows))
	pbar.close()
	conn.commit()
	conn.close()
	print("Done expanding accounts.")
