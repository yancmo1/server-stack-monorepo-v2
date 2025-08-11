---
applyTo: '**'
---


# User Memory

- Most, if not all, of the user's apps are docker containers.
- Always consider Docker as the primary runtime for the user's apps. When providing setup, testing, or deployment instructions, default to Docker-based workflows unless the user requests otherwise.
- The user wants to do as little as possible. The agent should handle the bulk of the work, keep the user updated, and be as independent as possible without breaking things.
- Server address: ssh yancmo@ubuntumac
- User has given permission to connect to this server as needed.
- Always start containers and test files, then stop and fix and start again and test again before calling the fixes complete.
- When struggling to get things working, always check the logs for errors first, base fixes on those errors, and continue checking logs until all problems are fixed.

- When making suggestions, always put emphasis on the best practice, explain why it is preferred, and mention other options only if they are valid. If alternatives are not needed, focus solely on best practice.
