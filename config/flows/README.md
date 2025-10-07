# Flow Configuration

This directory contains YAML configuration files that define conversation flows for the WhatsApp bot.

## Files

- **flows.yaml**: Main flow definitions (check_item, report_item, etc.)
- **handlers.yaml**: (Future) Handler registry mapping
- **states_config.yaml**: (Future) State machine configuration

## Flow Structure

Each flow in `flows.yaml` has the following structure:

```yaml
flows:
  flow_id:
    name: "Human-readable flow name"
    description: "Optional description"
    initial_step: "step_id"  # Starting step
    steps:
      step_id:
        prompt: "Message to user"  # Optional (required if no handler)
        prompt_type: "text|list|button"  # Default: "text"
        next: "next_step_id"  # Optional (if terminal step)
        handler: "handler_name"  # Optional (for terminal steps)
        handler_type: "query|command"  # Required if handler present
```

## Step Types

### Input Steps

Steps that prompt the user for input:

- `prompt`: The message shown to the user
- `prompt_type`: How to collect input
  - `text`: Free-form text input
  - `list`: Interactive list message (up to 10 items)
  - `button`: Reply buttons (up to 3 buttons)
- `next`: The next step to transition to

### Handler Steps

Terminal steps that execute business logic:

- `handler`: Name of the handler to execute (from handler registry)
- `handler_type`:
  - `query`: Read-only operations (searches, lookups)
  - `command`: Write operations (creating, updating data)

## Example

```yaml
flows:
  check_item:
    name: "Check if Stolen"
    initial_step: "category"
    steps:
      category:
        prompt: "What type of item?"
        prompt_type: "list"
        next: "description"
      description:
        prompt: "Describe the item"
        prompt_type: "text"
        next: "search"
      search:
        handler: "check_if_stolen"
        handler_type: "query"
```

## Validation

The flow configuration loader validates:

- All step references exist
- Initial step exists
- No circular dependencies
- Required fields are present
- Valid prompt_type and handler_type values

## Adding New Flows

1. Add flow definition to `flows.yaml`
2. Implement handlers in `src/application/`
3. Register handlers in handler registry
4. Test end-to-end flow

See [migration docs](../../docs/whatsapp-interactive-messages-migration.md) for detailed implementation guide.
