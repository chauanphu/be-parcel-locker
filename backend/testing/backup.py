import subprocess
from datetime import datetime

def backup_database():
    db_container_name = 'backend-db-1'  # Replace with your actual container name
    db_user = 'admin'                      # Replace with your database user
    db_password = '123123'              # Replace with your database password
    db_name = 'parcel'                      # Replace with your database name
    backup_file = f"backup_{db_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"

    command = f"docker exec {db_container_name} pg_dump -U {db_user} {db_name} > {backup_file}"

    try:
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        print(f"Backup successful! File saved as {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Backup failed: {e}")


if __name__ == "__main__":
    backup_database()