import argparse

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.users import User


def cli_parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new user and insert it in the DB."
    )
    parser.add_argument(
        "--username",
        "-u",
        action="store",
        type=str,
        help="Username.",
    )
    parser.add_argument(
        "--password",
        "-p",
        action="store",
        type=str,
        help="Password.",
    )
    return parser.parse_args()


def main(args: argparse.Namespace):
    engine = create_engine("sqlite:///./confidential_vms.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password = pwd_context.hash(args.password)
    user = User(username=args.username, hashed_password=password)
    session.add(user)
    session.commit()


if __name__ == "__main__":
    main(cli_parse())
