import strawberry
from strawberry.asgi import GraphQL

@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class ApstaServer:
    host: str
    port: int
    username: str
    password: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info) -> User:
        return User(name="Patrick", age=100)
    
    @strawberry.field
    def server(self, info) -> ApstaServer:
        return ApstaServer(port=443)

@strawberry.type
class Mutation1:
    @strawberry.mutation
    def create_user(self, info, name: str, age: int) -> User:
        return User(name=name, age=age)

@strawberry.type
class Mutation2:
    @strawberry.mutation
    def login_server(self, info, host: str, port: int, username: str, password: str) -> ApstaServer:
        return ApstaServer(host=host, port=port, username=username, password=password)


@strawberry.type
class Mutation(Mutation1, Mutation2):
    pass
    # @strawberry.mutation
    # def create_user(self, info, name: str, age: int) -> User:
    #     return User(name=name, age=age)


schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQL(schema)

