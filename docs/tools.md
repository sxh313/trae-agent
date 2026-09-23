# Tools

Trae Agent provides six built-in tools for software engineering tasks:

## str_replace_based_edit_tool

File and directory manipulation tool with persistent state.

**Operations:**
- `view` - Display file contents with line numbers, or list directory contents up to 2 levels deep
- `create` - Create new files (fails if file already exists)
- `str_replace` - Replace exact string matches in files (must be unique)
- `insert` - Insert text after a specified line number

**Key features:**
- Requires absolute paths (e.g., `/repo/file.py`)
- String replacements must match exactly, including whitespace
- Supports line range viewing for large files

## bash

Execute shell commands in a persistent session.

**Features:**
- Commands run in a shared bash session that maintains state
- 120-second timeout per command
- Session restart capability
- Background process support

**Usage notes:**
- Use `restart: true` to reset the session
- Avoid commands with excessive output
- Long-running commands should use `&` for background execution

## sequentialthinking

Structured problem-solving tool for complex analysis.

**Capabilities:**
- Break down problems into sequential thoughts
- Revise and branch from previous thoughts
- Dynamically adjust the number of thoughts needed
- Track thinking history and alternative approaches
- Generate and verify solution hypotheses

**Parameters:**
- `thought` - Current thinking step
- `thought_number` / `total_thoughts` - Progress tracking
- `next_thought_needed` - Continue thinking flag
- `is_revision` / `revises_thought` - Revision tracking
- `branch_from_thought` / `branch_id` - Alternative exploration

## task_done

Signal task completion with verification requirement.

**Purpose:**
- Mark tasks as successfully completed
- Must be called only after proper verification
- Encourages writing test/reproduction scripts

**Output:**
- Simple "Task done." message
- No parameters required

## json_edit_tool

Precise JSON file editing using JSONPath expressions.

**Operations:**
- `view` - Display entire file or content at specific JSONPaths
- `set` - Update existing values at specified paths
- `add` - Add new properties to objects or append to arrays
- `remove` - Delete elements at specified paths

**JSONPath examples:**
- `$.users[0].name` - First user's name
- `$.config.database.host` - Nested object property
- `$.items[*].price` - All item prices
- `$..key` - Recursive search for key

**Features:**
- Validates JSON syntax and structure
- Preserves formatting with pretty printing option
- Detailed error messages for invalid operations

## ckg

Query the code knowledge graph (CKG) of a codebase: an index of its functions, classes and
class methods, parsed with tree-sitter into a SQLite database.

**Commands:**
- `search_function` - Look up functions by identifier
- `search_class` - Look up classes by identifier
- `search_class_method` - Look up the methods of a class

**Parameters:**
- `command` - One of the three commands above (required)
- `path` - Absolute or relative path of the codebase directory to query (required)
- `identifier` - Function, class or method name to search for (required)
- `print_body` - Also print the matched body; on by default, set `false` for locations only

**Notes:**
- The first query on a directory builds the index; later calls reuse it. The index is keyed by a
  snapshot hash (`git status` when the directory is a repository, file metadata otherwise), so
  editing the codebase makes the next call rebuild it.
- Long results are truncated and marked with `<response clipped>`; multiple matches are returned
  until that limit.
- Supported file types are Python, Java, C/C++ (including headers) and JavaScript/TypeScript
  (`.js`, `.jsx`, `.ts`, `.tsx`).
- Known limitations, from `trae_agent/tools/ckg/ckg_database.py`: anonymous functions and arrow
  functions in JavaScript/TypeScript are not in the graph, and a subdirectory of an already
  indexed codebase gets its own fresh index rather than reusing the parent's.
