from jinja2 import Environment, FileSystemLoader
import db
import datetime
import os
import collections

file_loader = FileSystemLoader("template")
env = Environment(loader=file_loader)


def format_ts(ts, format="%Y-%m-%d"):
    return datetime.datetime.fromtimestamp(ts).strftime(format)


def format_ts_rfc3339(ts):
    """Format a timestamp as a date suitable for inclusion in Atom feeds."""
    date = datetime.datetime.fromtimestamp(ts)
    return date.isoformat() + ("Z" if date.utcoffset() is None else "")


env.filters["format_ts"] = format_ts
env.filters["format_ts_rfc3339"] = format_ts_rfc3339


def create_index(count=100, template="article.html"):
    posts = list(db.module().select_recent(count=count))
    posts = prepare_posts(posts)
    data = {"page": {}, "links": posts}

    with open(f"index.html", "w") as fp:
        fp.write(render(template, data))


def create_archives():
    # fetch all year-month combinations from links
    year_months = db.module().distinct_year_months()

    archives = collections.defaultdict(list)

    for year_month in year_months:
        (year, month) = year_month["year_month"].split("-")
        archives[year].append(month)

        posts = list(db.module().select_by_year_month(**year_month))
        posts = prepare_posts(posts)

        data = {
            "page": {"title": f'Archive: {year_month["year_month"]}'},
            "links": posts,
        }

        with open(f'{year_month["year_month"]}.html', "w") as fp:
            fp.write(render("links.html", data))

    data = {"page": {"title": "Archive"}, "year_months": archives}

    with open(f"archive.html", "w") as fp:
        fp.write(render("archive.html", data))


def create_feed(count=100):
    posts = list(db.module().select_recent(count=count))
    posts = prepare_posts(posts)
    data = {"links": posts}

    template = "atom.xml"

    with open(f"index.atom", "w") as fp:
        fp.write(render(template, data))


def prepare_posts(links):
    munged_links = []
    for link in links:
        clean_tags = link["tags"].split(" ")
        clean_tags = list(filter(lambda t: t not in ("+", "-"), clean_tags))
        link["clean_tags"] = sorted(clean_tags)
        print(link)
        if "quotable" in clean_tags:
            link["quotable"] = True

        munged_links.append(link)

    return munged_links


def render(template, data):
    template = env.get_template(template)
    return template.render(data)


def main():
    create_index()
    # create_archives()
    # create_feed()


if __name__ == "__main__":
    main()
