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
    *Wait **30 sec** before the server starts completely.*
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
    docker run --detach --name postgres \
    --env POSTGRES_USER=$POSTGRES_USER \
    --env POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    --env POSTGRES_DATABASE=$POSTGRES_DATABASE \
    --env POSTGRES_ROOT_PASSWORD=$POSTGRES_ROOT_PASSWORD \
    -p 5432:5432 postgres
    ```
* To stop container:
    ```bash
    docker stop postgres
    ```

### Database dump

***Only when DB containser is running***

* Create database:
    ```bash
    echo "CREATE DATABASE $POSTGRES_DATABASE;" | \
    docker exec -i bdis_landing_back-postgres-1 psql \
    -U $POSTGRES_USER -d postgres
    ```

* Create database tables from `sql_script.sql`:
    ```bash
    cat sql_script.sql | docker exec -i bdis_landing_back-postgres-1 psql \
    -U $POSTGRES_USER -d $POSTGRES_DATABASE -a
    ```

* Load data from `test_data.sql` to database:
    ```bash
    cat test_data.sql | docker exec -i bdis_landing_back-postgres-1 psql \
    -U $POSTGRES_USER -d $POSTGRES_DATABASE -a