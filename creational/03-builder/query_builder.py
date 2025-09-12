from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class SQLDialect(Enum):
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    SQLITE = "SQLite"

    def to_list() -> list[str]:
        return [dialect.value for dialect in SQLDialect]


@dataclass(frozen=True)
class SQLQuery:
    select: tuple[str, ...] = field(default_factory=tuple)
    table: str = ""
    where: tuple[tuple[str, ...]] = field(
        default_factory=tuple
    )  # (condition, param1, param2, ...)
    join: str = ""
    order_by: str = ""
    limit: int | None = None
    dielect: str = SQLDialect.MYSQL.value

    def query(self) -> str:
        return SQLFormatter.get_formatter(self.dielect).format_query(self)

    def parameters(self) -> tuple[any, ...]:
        params = []
        for _, *p in self.where:
            params.extend(p)
        return tuple(params)


class SQLFormatter(ABC):
    @abstractmethod
    def format_query(self, query: SQLQuery) -> str:
        pass

    @abstractmethod
    def format_limit(self, limit: int) -> str:
        pass

    @abstractmethod
    def qoute_identifier(self, identifier: str) -> str:
        pass

    @staticmethod
    def get_formatter(dialect: str) -> "SQLFormatter":
        if dialect == SQLDialect.MYSQL.value:
            return MySQLFormatter()
        elif dialect == SQLDialect.POSTGRESQL.value:
            return PostgreSQLFormatter()
        elif dialect == SQLDialect.SQLITE.value:
            return SQLiteFormatter()
        else:
            raise ValueError(f"Unsupported SQL dialect: {dialect}")


class MySQLFormatter(SQLFormatter):
    def format_query(self, query: SQLQuery) -> str:
        if not query.select or not query.table:
            raise ValueError("SELECT columns and FROM table must be specified")

        sql = f"SELECT {', '.join(self.qoute_identifier(col) for col in query.select)} FROM {self.qoute_identifier(query.table)}"

        if query.join:
            sql += f" JOIN {query.join}"

        if query.where:
            where_clauses = [cond for cond, *_ in query.where]
            sql += " WHERE " + " AND ".join(where_clauses)

        if query.order_by:
            sql += f" ORDER BY {self.qoute_identifier(query.order_by)}"

        if query.limit is not None:
            sql += f" {self.format_limit(query.limit)}"

        return sql + ";"

    def format_limit(self, limit: int) -> str:
        return f"LIMIT {limit}"

    def qoute_identifier(self, identifier: str) -> str:
        return f"`{identifier}`"


class PostgreSQLFormatter(SQLFormatter):
    def format_query(self, query: SQLQuery) -> str:
        if not query.select or not query.table:
            raise ValueError("SELECT columns and FROM table must be specified")

        sql = f'SELECT {", ".join(self.qoute_identifier(col) for col in query.select)} FROM {self.qoute_identifier(query.table)}'

        if query.join:
            sql += f" JOIN {query.join}"

        if query.where:
            where_clauses = [cond for cond, *_ in query.where]
            sql += " WHERE " + " AND ".join(where_clauses)

        if query.order_by:
            sql += f" ORDER BY {self.qoute_identifier(query.order_by)}"

        if query.limit is not None:
            sql += f" {self.format_limit(query.limit)}"

        return sql + ";"

    def format_limit(self, limit: int) -> str:
        return f"LIMIT {limit}"

    def qoute_identifier(self, identifier: str) -> str:
        return f'"{identifier}"'


class SQLiteFormatter(SQLFormatter):
    def format_query(self, query: SQLQuery) -> str:
        if not query.select or not query.table:
            raise ValueError("SELECT columns and FROM table must be specified")

        sql = f'SELECT {", ".join(self.qoute_identifier(col) for col in query.select)} FROM {self.qoute_identifier(query.table)}'

        if query.join:
            sql += f" JOIN {query.join}"

        if query.where:
            where_clauses = [cond for cond, *_ in query.where]
            sql += " WHERE " + " AND ".join(where_clauses)

        if query.order_by:
            sql += f" ORDER BY {self.qoute_identifier(query.order_by)}"

        if query.limit is not None:
            sql += f" {self.format_limit(query.limit)}"

        return sql + ";"

    def format_limit(self, limit: int) -> str:
        return f"LIMIT {limit}"

    def qoute_identifier(self, identifier: str) -> str:
        return f"[{identifier}]"


class SQLQueryBuilder:
    def __init__(self, dielect: str = SQLDialect.MYSQL.value) -> None:
        if dielect not in SQLDialect.to_list():
            raise ValueError(f"Dialect must be one of {SQLDialect.to_list()}")
        self.dielect = dielect
        self.reset()

    def reset(self) -> "SQLQueryBuilder":
        self._select: list[str] = []
        self._table: str = ""
        self._where: list[tuple[str, ...]] = []
        self._join: str = ""
        self._order_by: str = ""
        self._limit: int | None = None
        return self

    def select(self, *columns: str) -> "SQLQueryBuilder":
        if not columns:
            raise ValueError("At least one column must be specified for SELECT")
        self._select.extend(columns)
        return self

    def from_table(self, table: str) -> "SQLQueryBuilder":
        if not table:
            raise ValueError("Table name cannot be empty")
        self._table = table
        return self

    def where(self, condition: str, *params: any) -> "SQLQueryBuilder":
        if not condition:
            raise ValueError("WHERE condition cannot be empty")
        self._where.append((condition, *params))
        return self

    def join(self, table: str, on_condition: str) -> "SQLQueryBuilder":
        if not table or not on_condition:
            raise ValueError("JOIN table and ON condition cannot be empty")
        self._join = f"{table} ON {on_condition}"
        return self

    def order_by(self, column: str) -> "SQLQueryBuilder":
        if not column:
            raise ValueError("ORDER BY column cannot be empty")
        self._order_by = column
        return self

    def limit(self, limit: int) -> "SQLQueryBuilder":
        if limit <= 0:
            raise ValueError("LIMIT must be a positive integer")
        self._limit = limit
        return self

    def build(self) -> SQLQuery:
        self.validate()
        query = SQLQuery(
            select=tuple(self._select),
            table=self._table,
            where=tuple(self._where),
            join=self._join,
            order_by=self._order_by,
            limit=self._limit,
            dielect=self.dielect,
        )
        self.reset()
        return query

    def copy(self) -> "SQLQueryBuilder":
        new_builder = SQLQueryBuilder()
        new_builder._select = self._select.copy()
        new_builder._table = self._table
        new_builder._where = self._where
        new_builder._order_by = self._order_by
        new_builder._limit = self._limit
        return new_builder

    def validate(self) -> None:
        errors = []
        if not self._table:
            errors.append("Table name is not set")
        if errors:
            raise ValueError("Validation errors: " + "; ".join(errors))


class SQLQueryDirector:
    def __init__(self, builder: SQLQueryBuilder) -> None:
        self._builder = builder

    @property
    def builder(self) -> SQLQueryBuilder:
        return self._builder

    @builder.setter
    def builder(self, builder: SQLQueryBuilder) -> None:
        self._builder = builder

    def simple_select_all(self, table: str) -> SQLQuery:
        return self._builder.reset().select("*").from_table(table).build()

    def user_by_age_range(self, table: str, min_age: int, max_age: int) -> SQLQuery:
        return (
            self._builder.reset()
            .select("id", "name", "age")
            .from_table(table)
            .where("age >= %s", min_age)
            .where("age <= %s", max_age)
            .order_by("age")
            .build()
        )

    def user_orders_report(
        self, user_table: str, orders_table: str, min_total: float
    ) -> SQLQuery:
        return (
            self._builder.reset()
            .select(f"{user_table}.id", f"{user_table}.name", f"{orders_table}.total")
            .from_table(user_table)
            .join(orders_table, f"{user_table}.id = {orders_table}.user_id")
            .where(f"{orders_table}.total >= %s", min_total)
            .order_by(f"{orders_table}.total")
            .build()
        )


if __name__ == "__main__":
    for dielect in SQLDialect.to_list():
        builder = SQLQueryBuilder(dielect)
        director = SQLQueryDirector(builder)

        print(f"\n-- {dielect} Simple Select All --")
        query1 = director.simple_select_all("users")
        print("Query:", query1.query())
        print("Parameters:", query1.parameters())

        print(f"\n-- {dielect} Users by Age Range --")
        query2 = director.user_by_age_range("users", 18, 30)
        print("Query:", query2.query())
        print("Parameters:", query2.parameters())

        print(f"\n-- {dielect} User Orders Report --")
        query3 = director.user_orders_report("users", "orders", 100.0)
        print("Query:", query3.query())
        print("Parameters:", query3.parameters())
