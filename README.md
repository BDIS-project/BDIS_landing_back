## First steps

1. Create `.env` file and write the following lines into it:
    ```
    POSTGRES_DATABASE=zlagoda
    POSTGRES_USER=django-admin
    POSTGRES_PASSWORD=<django-db-password>
    POSTGRES_ROOT_PASSWORD=<db-root-password>
    ```

    **Always check for this file, as it isn`t uploaded to the remote repository**

<!-- 2. Soon -->


## Full backend launch

* Create and run docker container
    ```bash
    docker compose up --build -d
    ```
    *Wait **10 sec** before the server starts completely.*
* To stop containers, use the following commands:
    ```bash
    docker compose stop
    ```
* To remove containers:
    ```bash
    docker compose rm
    ```

## Postgres

* Create and run container:
    ```bash
    docker run --detach --name mariadb \
    --env POSTGRES_USER=$POSTGRES_USER \
    --env POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    --env POSTGRES_DATABASE=$POSTGRES_DATABASE \
    --env POSTGRES_ROOT_PASSWORD=$POSTGRES_ROOT_PASSWORD \
    -p 3306:3306 mariadb
    ```
* To stop container:
    ```bash
    docker stop mariadb
    ```

### Database dump

***Only when DB containser is running***

* Save database to `dump.sql` file:
    ```bash
    docker exec -it mariadb mariadb-dump \
    --user=$POSTGRES_USER --password=$POSTGRES_PASSWORD \
    $POSTGRES_DATABASE > dump.sql
    ```
* Load `dump.sql` file to database:
    ```bash
    docker exec -i mariadb mariadb \
    --user=$POSTGRES_USER \
    --password=$POSTGRES_PASSWORD \
    $POSTGRES_DATABASE < dump.sql
    ```