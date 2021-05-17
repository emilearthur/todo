Running:coverage test ``````







# Requirements  and installation
## Via Cloning The Repository 
```
# Make user you have docker installed.

# Clone the app 
git clone https://github.com/emilearthur/todo.git

# Setup Env
Follow the format specified in the .env.template file

# Running docker to start application
docker-compose up --build

```

# Testing
* Check-in docker environment after build. Run the command below
```docker exec -it <CONTAINER ID> bash```

* To run and check for test coverage. Run the command below
```py.test -v --cov``` 
    * for term-missing
    `pytest --cov-report term-missing --cov=. tests/`

*  To obtain coverage report. Run command below:
```coverage report```

* To obtain html browser report. Run command below:
```coverage html``` or ```pytest --cov-report html  --cov=. tests/```

    ```A folder titled html_coverage_report will be generated. Open it and copy the path  of index.html and paste it in your browser. ```

* To generate report in xml format. Run command below:
```py.test  --junitxml=tests_output/test_repot.xml```


# View API documentation:

To view API documentation enter ```http://localhost:8000/docs``` in your browser after installation and docker build. 

# Technologies 
## Backend
* [FastAPI](https://fastapi.tiangolo.com/) is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
* [SQLAlchemy](https://www.sqlalchemy.org/)is the Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
* [Alembic](https://alembic.sqlalchemy.org/en/latest/) is a lightweight database migration tool for usage with SQLAlchemy DB toolkit for Python.
* [PyTest](https://docs.pytest.org/en/6.2.x/) is a framework that makes building simple and scalable tests easy.
* uvicorn
*Postgres DB - Main Database.
* Redis - For Email Verfication Implementation.