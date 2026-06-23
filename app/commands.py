import click
from flask.cli import with_appcontext

from app import db
from app.models.user import User


@click.command("create-user")
@click.option("--username", prompt=True, help="Unique login name.")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password (entered securely and stored only as a hash).",
)
@click.option(
    "--role",
    type=click.Choice(["admin", "manager", "staff"], case_sensitive=False),
    prompt=True,
)
@click.option("--full-name", prompt=True)
@click.option(
    "--update",
    is_flag=True,
    help="Update an existing user's password and profile.",
)
@with_appcontext
def create_user_command(username, password, role, full_name, update):
    """Create or explicitly update a database-backed login account."""
    username = username.strip()
    full_name = full_name.strip()
    role = role.lower()

    if not username:
        raise click.ClickException("Username cannot be empty.")
    if not full_name:
        raise click.ClickException("Full name cannot be empty.")
    if len(password) < 12:
        raise click.ClickException("Password must contain at least 12 characters.")

    db.create_all()
    user = User.query.filter_by(username=username).first()
    user_existed = user is not None
    if user and not update:
        raise click.ClickException(
            f"User '{username}' already exists. Use --update to change it."
        )

    if not user:
        user = User(username=username)
        db.session.add(user)

    user.full_name = full_name
    user.role = role
    user.status = "Active"
    user.set_password(password)
    db.session.commit()

    action = "Updated" if user_existed else "Created"
    click.echo(f"{action} user '{username}' in the database.")


@click.command("list-users")
@with_appcontext
def list_users_command():
    """List database users without exposing password hashes."""
    db.create_all()
    users = User.query.order_by(User.username).all()
    if not users:
        click.echo("No users exist. Run 'flask --app run create-user'.")
        return

    for user in users:
        click.echo(f"{user.username}\t{user.role}\t{user.status}\t{user.full_name}")
