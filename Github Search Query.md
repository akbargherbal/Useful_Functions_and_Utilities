# Basic Queries
- Search in Vue language repos and in package.json files for specific string
```go
language:vue pinia in:file filename:package.json
language:vue pinia in:file filename:package.json stars:2..1000 created:>2021
```

Search `<script setup` in .vue files
```go
"<script setup" in:file filename:*.vue
```


## Queries

1. `react in:name,description` - This query will search for repositories with "react" in their name or description.
2. `react in:readme` - This query will search for repositories with "react" mentioned in their README file.
3. `react language:javascript` - This query will search for repositories with "react" in their name or description and are written in JavaScript.
4. `react pushed:>=2022-01-01` - This query will search for repositories with "react" in their name or description and have been pushed to on or after January 1st, 2022.
5. `react stars:>=100` - This query will search for repositories with "react" in their name or description and have at least 100 stars.
6. `react forks:>=50` - This query will search for repositories with "react" in their name or description and have at least 50 forks.
7. `react topic:web-development` - This query will search for repositories with "react" in their name or description and have the topic "web-development".

## Advanced Queries

1. `react in:name,description filename:package.json "next" in:file` - This query will search for repositories with "react" in their name or description and have the package "next" mentioned in their package.json file.
2. `react in:name,description path:/src` - This query will search for repositories with "react" in their name or description and have a "src" folder at the root level.
3. `react in:name,description filename:.env.example` - This query will search for repositories with "react" in their name or description and have a ".env.example" file.
4. `react in:name,description filename:docker-compose.yml` - This query will search for repositories with "react" in their name or description and have a "docker-compose.yml" file.
5. `react in:name,description filename:CONTRIBUTING.md` - This query will search for repositories with "react" in their name or description and have a "CONTRIBUTING.md" file.
6. `react in:name,description filename:LICENSE MIT` - This query will search for repositories with "react" in their name or description and have an MIT license.
7. `react in:name,description filename:.github/ISSUE_TEMPLATE` - This query will search for repositories with "react" in their name or description and have an issue template set up.
