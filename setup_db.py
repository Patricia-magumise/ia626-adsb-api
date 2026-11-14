import pymysql
import yaml

with open("config.yml", "r") as file:
    db_config = yaml.safe_load(file)["mysql"]

with open("setup_tables.sql", "r") as file:
    lines = [ln for ln in file if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "".join(lines).split(";") if s.strip()]

conn = pymysql.connect(**db_config)
with conn.cursor() as cur:
    for sql in statements:
        cur.execute(sql)
    conn.commit()
    cur.execute("SELECT `token` FROM `magumip_auth`;")
    print("Tables ready. Valid keys:", [row[0] for row in cur.fetchall()])
conn.close()
