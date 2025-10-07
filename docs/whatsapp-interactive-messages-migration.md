# WhatsApp Interactive Messages Migration

**Document Version:** 2.0
**Created:** 2025-10-07
**Updated:** 2025-10-07
**Status:** Planning

## Overview

This document outlines the migration to:

1. **Meta's official WhatsApp Cloud API interactive messages** (reply buttons and lists)
2. **Configuration-driven conversation flows** (YAML-based, no code changes for new flows)

The migration will transform the bot from hardcoded 11-state flows to a flexible, configuration-driven system where new conversations (e.g., "Contact Us", "Request Category") can be added via YAML files only.

## Current State Analysis

### Current Architecture (Hardcoded Flows)

```text
11 States: IDLE → MAIN_MENU → {CHECKING_*, REPORTING_*} → COMPLETE/CANCELLED
477 lines of hardcoded flow logic in message_router.py
Text parsing for categories and menu choices
24 state transitions manually defined
```

**Components:**

- [src/presentation/bot/states.py](../src/presentation/bot/states.py) - 11 hardcoded states
- [src/presentation/bot/message_router.py](../src/presentation/bot/message_router.py) - 477 lines of flow logic
- [src/presentation/bot/response_builder.py](../src/presentation/bot/response_builder.py) - Text-only responses
- [src/infrastructure/whatsapp/client.py](../src/infrastructure/whatsapp/client.py) - Only `send_text_message()`

### Target Architecture (Configuration-Driven)

```text
5-6 States: IDLE → MAIN_MENU → ACTIVE_FLOW → COMPLETE/CANCELLED
Flow definitions in config/flows/flows.yaml
Generic flow execution engine
Interactive messages (buttons/lists) via Meta's official API
```

**New Components:**

- `config/flows/flows.yaml` - All conversation flows defined here
- `config/flows/handlers.yaml` - Handler registry mapping
- `src/infrastructure/config/flow_config_loader.py` - YAML loader + validator
- `src/infrastructure/handlers/handler_registry.py` - Dynamic handler loading
- `src/presentation/bot/flow_engine.py` - Generic flow execution engine

## WhatsApp Interactive Messages (Meta Cloud API Only)

**We use ONLY Meta's official WhatsApp Cloud API** - no third-party libraries or unofficial APIs.

### 1. Reply Buttons (Up to 3 buttons)

**Use Cases:** Main menu, yes/no confirmations, navigation

**API Structure:**

```json
{
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": { "text": "Message text" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "button_1", "title": "Button 1" } },
        { "type": "reply", "reply": { "id": "button_2", "title": "Button 2" } },
        { "type": "reply", "reply": { "id": "button_3", "title": "Button 3" } }
      ]
    }
  }
}
```

**Webhook Callback:**

```json
{
  "interactive": {
    "type": {
      "button_reply": {
        "id": "button_1",
        "title": "Button 1"
      }
    }
  }
}
```

### 2. List Messages (Up to 10 items across sections)

**Use Cases:** Category selection, multi-option menus

**API Structure:**

```json
{
  "type": "interactive",
  "interactive": {
    "type": "list",
    "header": { "type": "text", "text": "Header" },
    "body": { "text": "Body text" },
    "action": {
      "button": "View options",
      "sections": [
        {
          "title": "Section 1",
          "rows": [
            { "id": "item_1", "title": "Item 1", "description": "Description" }
          ]
        }
      ]
    }
  }
}
```

**Webhook Callback:**

```json
{
  "interactive": {
    "type": {
      "list_reply": {
        "id": "item_1",
        "title": "Item 1",
        "description": "Description"
      }
    }
  }
}
```

## Configuration-Driven Flow Architecture

### Example: Complete Flow in YAML

```yaml
flows:
  contact_us:
    name: "Contact Us"
    description: "User wants to contact support"
    version: "1.0"

    triggers:
      - menu_choice: "3"
      - keyword: "contact"

    slots:
      - name: message
        type: string
        required: true
        prompt: "How can we help you?"
        validation:
          type: string
          min_length: 10
          max_length: 1000

      - name: email
        type: email
        required: false
        prompt: "Email for follow-up? (Type 'skip' if not needed)"
        allow_skip: true

    steps:
      - id: collect_message
        type: collect
        slot: message
        next: collect_email

      - id: collect_email
        type: collect
        slot: email
        next: send_to_support

      - id: send_to_support
        type: action
        handler: "support_handler"
        action: "create_ticket"
        params:
          phone_number: "{context.phone_number}"
          message: "{slots.message}"
          email: "{slots.email}"
        next: show_confirmation

      - id: show_confirmation
        type: response
        message: |
          ✅ Thank you! Your message has been received.
          Reference: {action.send_to_support.ticket_id}
        next: complete

      - id: complete
        type: terminal
        state: complete
```

**No code changes needed to add this flow!** Just add to YAML, define handler in `handlers.yaml`, and implement the handler itself.

## Migration Strategy

### Dependency-Based Issue Order (Not Arbitrary Phases)

Issues are organized by **logical dependencies**, not arbitrary groupings. Work on any issue immediately after its dependencies are complete.

### Dependency Graph

```bash
┌───────────────────────────────────────────────────────────────────┐
│ Can Start Immediately (No Dependencies)                           │
├───────────────────────────────────────────────────────────────────┤
│ Issue #103: WhatsApp Client (Meta API)                           │
│ Issue #104: Webhook Parsing                                      │
│ Issue #105: Response Builder                                     │
│ Issue #108: Config Loader                                        │
│ Issue #109: Handler Registry                                     │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #103, #104, #105                                         │
├───────────────────────────────────────────────────────────────────┤
│ Issue #106: Main Menu Buttons                                    │
│ Issue #107: Category Lists                                       │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #108, #109                                               │
├───────────────────────────────────────────────────────────────────┤
│ Issue #110: Flow Execution Engine                                │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #110                                                     │
├───────────────────────────────────────────────────────────────────┤
│ Issue #111: Migrate Check Flow to Config                         │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #111                                                     │
├───────────────────────────────────────────────────────────────────┤
│ Issue #112: Migrate Report Flow to Config                        │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #112 (Demo of extensibility)                            │
├───────────────────────────────────────────────────────────────────┤
│ Issue #113: Add Contact Us Flow (Config Only!)                   │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #113 (All flows migrated)                               │
├───────────────────────────────────────────────────────────────────┤
│ Issue #114: Simplify State Machine (Remove Old States)           │
└───────────────────────────────────────────────────────────────────┘
                    ↓
┌───────────────────────────────────────────────────────────────────┐
│ Requires #114 (Final validation)                                 │
├───────────────────────────────────────────────────────────────────┤
│ Issue #115: Update Integration & E2E Tests                       │
└───────────────────────────────────────────────────────────────────┘
```

---

## Implementation Issues

### Issue #103: Add Interactive Message Support to WhatsApp Client

**GitHub Issue:** [#103](https://github.com/barry47products/is-it-stolen/issues/103)
**Dependencies:** None (start here!)
**Branch:** `feature/interactive-whatsapp-client`

**Files:**

- `src/infrastructure/whatsapp/client.py` (modify)
- `tests/unit/infrastructure/whatsapp/test_client.py` (modify)

**Description:**
Add methods to WhatsApp client for sending interactive messages using **Meta's official WhatsApp Cloud API only**.

**API Documentation:**

- [Reply Buttons](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-reply-buttons-messages)
- [List Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-list-messages)

**Tasks:**

1. ✅ Write failing tests for `send_reply_buttons(to, body, buttons[])`
2. ✅ Implement `send_reply_buttons()` with Meta API payload
3. ✅ Write failing tests for `send_list_message(to, body, button_text, sections[])`
4. ✅ Implement `send_list_message()` with Meta API payload
5. ✅ Update type hints and docstrings
6. ✅ Run `make check` (100% coverage, mypy, ruff)
7. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test sending 1, 2, 3 button messages
- ✅ Test sending list with single section
- ✅ Test sending list with multiple sections
- ✅ Test error handling for invalid payloads
- ✅ Test rate limiting and retries

**Acceptance Criteria:**

- [x] `send_reply_buttons()` sends correct Meta API payload
- [x] `send_list_message()` sends correct Meta API payload
- [x] Payloads match official Meta specifications exactly
- [x] All tests pass with 100% coverage
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #104: Add Interactive Message Parsing to Webhook Handler

**GitHub Issue:** [#104](https://github.com/barry47products/is-it-stolen/issues/104)
**Dependencies:** None (parallel with #103)
**Branch:** `feature/interactive-webhook-parsing`

**Files:**

- `src/infrastructure/whatsapp/webhook_handler.py` (modify)
- `tests/unit/infrastructure/whatsapp/test_webhook_handler.py` (modify)

**Description:**
Parse interactive message callbacks from Meta's WhatsApp Cloud API webhooks.

**API Documentation:**

- [Webhook Components](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components)

**Tasks:**

1. ✅ Write failing tests for parsing `button_reply` webhooks
2. ✅ Implement button reply parsing (extract `id` and `title`)
3. ✅ Write failing tests for parsing `list_reply` webhooks
4. ✅ Implement list reply parsing (extract `id`, `title`, `description`)
5. ✅ Update `_add_message_content()` to handle interactive types
6. ✅ Keep backward compatibility with text messages
7. ✅ Run `make check` (100% coverage, mypy, ruff)
8. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test parsing button reply with ID and title
- ✅ Test parsing list reply with ID, title, description
- ✅ Test fallback to text parsing for non-interactive messages
- ✅ Test error handling for malformed interactive payloads

**Acceptance Criteria:**

- [x] Webhook handler extracts `button_reply.id` and `button_reply.title`
- [x] Webhook handler extracts `list_reply.id`, `list_reply.title`, `list_reply.description`
- [x] Backward compatible with text message parsing
- [x] All tests pass with 100% coverage
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #105: Add Interactive Response Builder Methods

**GitHub Issue:** [#105](https://github.com/barry47products/is-it-stolen/issues/105)
**Dependencies:** None (parallel with #103, #104)
**Branch:** `feature/interactive-response-builder`

**Files:**

- `src/presentation/bot/response_builder.py` (modify)
- `tests/unit/presentation/bot/test_response_builder.py` (modify)

**Description:**
Add methods to ResponseBuilder for creating interactive message payloads.

**Tasks:**

1. ✅ Write failing tests for `build_reply_buttons(body, buttons[])`
2. ✅ Implement `build_reply_buttons()` returning Meta API dict
3. ✅ Write failing tests for `build_list_message(body, button_text, sections[])`
4. ✅ Implement `build_list_message()` returning Meta API dict
5. ✅ Add helper for building category list
6. ✅ Validate button/row limits (max 3 buttons, max 10 rows)
7. ✅ Run `make check` (100% coverage, mypy, ruff)
8. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test building 1, 2, 3 button payloads
- ✅ Test building list with single section
- ✅ Test building list with multiple sections
- ✅ Test validation errors for exceeding limits

**Acceptance Criteria:**

- [x] `build_reply_buttons()` returns valid Meta API payload
- [x] `build_list_message()` returns valid Meta API payload
- [x] Methods validate button/row limits
- [x] All tests pass with 100% coverage
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #106: Migrate Main Menu to Reply Buttons

**GitHub Issue:** [#106](https://github.com/barry47products/is-it-stolen/issues/106)
**Dependencies:** [#103](https://github.com/barry47products/is-it-stolen/issues/103), [#104](https://github.com/barry47products/is-it-stolen/issues/104), [#105](https://github.com/barry47products/is-it-stolen/issues/105)
**Branch:** `feature/interactive-main-menu`

**Files:**

- `src/presentation/bot/message_router.py` (modify)
- `src/presentation/bot/response_builder.py` (modify)
- `tests/unit/presentation/bot/test_message_router.py` (modify)

**Description:**
Replace text-based main menu with reply buttons (Check / Report / Cancel).

**Tasks:**

1. ✅ Add `build_welcome_buttons()` method to ResponseBuilder
2. ✅ Update webhook_receiver to extract `button_id` from parsed messages
3. ✅ Update `_handle_idle()` to return interactive button payload
4. ✅ Write failing tests for button click handling
5. ✅ Update `_handle_main_menu()` to parse `button_reply.id`
6. ✅ Keep backward compatibility with text "1" and "2"
7. ✅ Update message_processor to send interactive messages
8. ✅ Run `make check` (100% coverage, mypy, ruff)
9. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test `build_welcome_buttons()` returns correct payload
- ✅ Test IDLE sends interactive reply buttons
- ✅ Test clicking "check_item" button routes correctly
- ✅ Test clicking "report_item" button routes correctly
- ✅ Test fallback text parsing still works ("1", "2")

**Acceptance Criteria:**

- [x] `build_welcome_buttons()` method implemented
- [x] Welcome message uses reply buttons
- [x] Button clicks route correctly
- [x] Backward compatible with text input
- [x] All tests pass with 100% coverage
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #107: Migrate Category Selection to List Messages

**GitHub Issue:** [#107](https://github.com/barry47products/is-it-stolen/issues/107)
**Dependencies:** [#103](https://github.com/barry47products/is-it-stolen/issues/103), [#104](https://github.com/barry47products/is-it-stolen/issues/104), [#105](https://github.com/barry47products/is-it-stolen/issues/105)
**Branch:** `feature/interactive-category-selection`

**Files:**

- `src/presentation/bot/message_router.py` (modify)
- `src/presentation/bot/response_builder.py` (modify)
- `tests/unit/presentation/bot/test_message_router.py` (modify)

**Description:**
Replace text-based category input with interactive list (Bicycle / Phone / Laptop / Car / Other).

**Tasks:**

1. ✅ Write failing tests for category list in check flow
2. ✅ Update category prompt to send list message
3. ✅ Update category parsing to handle `list_reply.id`
4. ✅ Repeat for reporting flow
5. ✅ Keep backward compatibility with text category names
6. ✅ Run `make check` (100% coverage, mypy, ruff)
7. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test check flow sends category list (4 options)
- ✅ Test report flow sends category list (4 options)
- ✅ Test selecting list item extracts correct category
- ✅ Test fallback text parsing still works

**Acceptance Criteria:**

- [x] Category prompts use list messages
- [x] List selections correctly extract ItemCategory
- [x] Backward compatible with text category names
- [x] All tests pass with 100% coverage
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #108: Create Configuration Loader Infrastructure

**GitHub Issue:** [#108](https://github.com/barry47products/is-it-stolen/issues/108)
**Dependencies:** None (parallel with #103-107)
**Branch:** `feature/config-loader-infrastructure`

**Files:**

- `src/infrastructure/config/flow_config_loader.py` (new)
- `tests/unit/infrastructure/config/test_flow_config_loader.py` (new)
- `config/flows/flows.yaml` (new)
- `config/flows/states_config.yaml` (new)

**Description:**
Build infrastructure to load and validate conversation flows from YAML. This is the foundation for configuration-driven flows.

**Tasks:**

1. ✅ Write failing tests for FlowConfigLoader
2. ✅ Implement Pydantic models for flow configuration
3. ✅ Implement YAML loader with validation
4. ✅ Create sample flows.yaml with check/report flows
5. ⏸️ Create states_config.yaml with state definitions (deferred to future issue)
6. ✅ Add configuration validation (reachability, references)
7. ✅ Run `make check` (96% coverage, mypy, ruff)
8. ✅ Commit and create PR

**Test Coverage:**

- ✅ Test loading valid flow configurations
- ✅ Test validation catches invalid references
- ✅ Test validation catches circular dependencies
- ✅ Test validation catches missing required fields
- ✅ Test error handling for malformed YAML
- ✅ Test validation of prompt_type and handler_type
- ✅ Test handling of file not found
- ✅ Test multiple flows in single file

**Acceptance Criteria:**

- [x] FlowConfigLoader loads flows from YAML
- [x] Pydantic validates all configuration fields
- [x] Validation catches structural errors
- [x] All tests pass with 96% coverage (13 tests)
- [x] No mypy or ruff errors
- [x] Pre-commit checks pass

---

### Issue #109: Create Handler Registry for Dynamic Loading

**GitHub Issue:** [#109](https://github.com/barry47products/is-it-stolen/issues/109)
**Dependencies:** None (parallel with #103-108)
**Branch:** `feature/handler-registry`

**Files:**

- `src/infrastructure/handlers/handler_registry.py` (new)
- `tests/unit/infrastructure/handlers/test_handler_registry.py` (new)
- `config/flows/handlers.yaml` (new)

**Description:**
Build handler registry that dynamically loads command/query handlers based on configuration. Decouples flow configuration from handler implementation.

**Tasks:**

1. Write failing tests for HandlerRegistry
2. Implement dynamic class loading from module paths
3. Implement dependency injection for handler dependencies
4. Create handlers.yaml with existing handlers mapped
5. Add service registry for shared dependencies
6. Support singleton pattern for services
7. Run `make check` (100% coverage, mypy, ruff)
8. Commit and create PR

**Test Coverage:**

- Test loading handler by name
- Test dependency injection works correctly
- Test singleton services cached properly
- Test error handling for missing handlers/services
- Test error handling for invalid class paths

**Acceptance Criteria:**

- [ ] HandlerRegistry loads handlers from YAML
- [ ] Handlers can declare dependencies in configuration
- [ ] Services support singleton pattern
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #110: Build Generic Flow Execution Engine

**GitHub Issue:** [#110](https://github.com/barry47products/is-it-stolen/issues/110)
**Dependencies:** [#108](https://github.com/barry47products/is-it-stolen/issues/108) (Config Loader), [#109](https://github.com/barry47products/is-it-stolen/issues/109) (Handler Registry)
**Branch:** `feature/flow-execution-engine`

**Files:**

- `src/presentation/bot/flow_engine.py` (new)
- `tests/unit/presentation/bot/test_flow_engine.py` (new)

**Description:**
Create generic flow execution engine that interprets flow configurations and executes steps. This replaces hardcoded flow logic.

**Tasks:**

1. Write failing tests for FlowEngine
2. Implement step execution for each type (collect, action, response, terminal)
3. Implement slot validation and parsing
4. Implement template variable substitution
5. Implement parameter building for handler calls
6. Add error handling and recovery
7. Run `make check` (100% coverage, mypy, ruff)
8. Commit and create PR

**Test Coverage:**

- Test executing collect steps with validation
- Test executing action steps with handler calls
- Test executing response steps with templates
- Test executing terminal steps
- Test template variable substitution
- Test error handling for invalid steps

**Acceptance Criteria:**

- [ ] FlowEngine executes steps from configuration
- [ ] Collect steps validate input and store in context
- [ ] Action steps call handlers with correct parameters
- [ ] Template variables substituted correctly
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #111: Migrate Check Flow to Configuration

**GitHub Issue:** [#111](https://github.com/barry47products/is-it-stolen/issues/111)
**Dependencies:** [#110](https://github.com/barry47products/is-it-stolen/issues/110) (Flow Engine)
**Branch:** `feature/migrate-check-flow-to-config`

**Files:**

- `config/flows/flows.yaml` (modify - add complete check flow)
- `src/presentation/bot/message_router.py` (modify - use flow engine)
- `tests/unit/presentation/bot/test_message_router.py` (modify)

**Description:**
Migrate "check if stolen" flow from hardcoded logic to YAML configuration, using flow engine for execution.

**Tasks:**

1. Define complete check flow in flows.yaml
2. Write failing tests for flow-engine-based routing
3. Update message_router to use flow_engine for check flow
4. Keep backward compatibility during migration
5. Test end-to-end check flow
6. Run `make check` (100% coverage, mypy, ruff)
7. Commit and create PR

**Test Coverage:**

- Test check flow executes from configuration
- Test all check flow steps work correctly
- Test data collection and handler invocation
- Test error handling in check flow

**Acceptance Criteria:**

- [ ] Check flow defined completely in flows.yaml
- [ ] Message router uses flow engine for check flow
- [ ] All check flow functionality preserved
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #112: Migrate Report Flow to Configuration

**GitHub Issue:** [#112](https://github.com/barry47products/is-it-stolen/issues/112)
**Dependencies:** [#111](https://github.com/barry47products/is-it-stolen/issues/111) (Check Flow Migration)
**Branch:** `feature/migrate-report-flow-to-config`

**Files:**

- `config/flows/flows.yaml` (modify - add complete report flow)
- `src/presentation/bot/message_router.py` (modify - use flow engine)
- `tests/unit/presentation/bot/test_message_router.py` (modify)

**Description:**
Migrate "report stolen item" flow from hardcoded logic to YAML configuration.

**Tasks:**

1. Define complete report flow in flows.yaml
2. Write failing tests for flow-engine-based report routing
3. Update message_router to use flow_engine for report flow
4. Test end-to-end report flow
5. Run `make check` (100% coverage, mypy, ruff)
6. Commit and create PR

**Test Coverage:**

- Test report flow executes from configuration
- Test all report flow steps work correctly
- Test data collection, validation, and handler invocation
- Test error handling in report flow

**Acceptance Criteria:**

- [ ] Report flow defined completely in flows.yaml
- [ ] Message router uses flow engine for report flow
- [ ] All report flow functionality preserved
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #113: Add Contact Us Flow via Configuration (Demo)

**GitHub Issue:** [#113](https://github.com/barry47products/is-it-stolen/issues/113)
**Dependencies:** [#112](https://github.com/barry47products/is-it-stolen/issues/112) (Report Flow Migration)
**Branch:** `feature/add-contact-us-flow`

**Files:**

- `config/flows/flows.yaml` (modify - add contact us flow)
- `config/flows/handlers.yaml` (modify - add support handler)
- `src/application/commands/create_support_ticket.py` (new)
- `tests/unit/application/commands/test_create_support_ticket.py` (new)

**Description:**
Add a new "Contact Us" flow **entirely through configuration** to demonstrate extensibility. This flow collects a message and optional email, then creates a support ticket.

**Tasks:**

1. Define contact_us flow in flows.yaml
2. Add support_handler to handlers.yaml
3. Implement CreateSupportTicketHandler (minimal)
4. Write tests for support ticket handler
5. Test complete contact flow end-to-end
6. Run `make check` (100% coverage, mypy, ruff)
7. Commit and create PR

**Test Coverage:**

- Test contact flow defined in configuration
- Test flow engine executes contact flow
- Test support ticket handler creates tickets
- Test optional email field handling

**Acceptance Criteria:**

- [ ] **Contact Us flow added via configuration only** (no flow logic changes!)
- [ ] Support ticket handler implemented and tested
- [ ] Flow works end-to-end
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #114: Simplify State Machine (Remove Obsolete States)

**GitHub Issue:** [#114](https://github.com/barry47products/is-it-stolen/issues/114)
**Dependencies:** [#113](https://github.com/barry47products/is-it-stolen/issues/113) (All flows migrated)
**Branch:** `feature/simplify-state-machine`

**Files:**

- `src/presentation/bot/states.py` (modify)
- `src/presentation/bot/message_router.py` (modify)
- `tests/unit/presentation/bot/test_states.py` (modify)
- `tests/unit/presentation/bot/test_state_machine.py` (modify)

**Description:**
Remove obsolete hardcoded states now that flows are configuration-driven. Simplify to: IDLE, MAIN_MENU, ACTIVE_FLOW, COMPLETE, CANCELLED.

**Tasks:**

1. Write tests for simplified state set
2. Remove CHECKING*\* and REPORTING*\* states
3. Add generic ACTIVE_FLOW state for any running flow
4. Update STATE_TRANSITIONS to simplified model
5. Remove hardcoded flow methods from message_router
6. Update all affected tests
7. Run `make check` (100% coverage, mypy, ruff)
8. Commit and create PR

**Test Coverage:**

- Test simplified state transitions
- Test ACTIVE_FLOW works for any configured flow
- Test no hardcoded flow logic remains

**Acceptance Criteria:**

- [ ] State machine reduced to 5 states
- [ ] All hardcoded flow methods removed
- [ ] All flows execute via flow engine
- [ ] All tests pass with 100% coverage
- [ ] No mypy or ruff errors
- [ ] Pre-commit checks pass

---

### Issue #115: Update Integration and E2E Tests

**GitHub Issue:** [#115](https://github.com/barry47products/is-it-stolen/issues/115)
**Dependencies:** [#114](https://github.com/barry47products/is-it-stolen/issues/114) (State Machine Cleanup)
**Branch:** `feature/update-integration-e2e-tests`

**Files:**

- `tests/integration/presentation/bot/test_conversation_integration.py` (modify)
- `tests/e2e/presentation/test_conversation_flows.py` (modify)

**Description:**
Update all integration and E2E tests for configuration-driven flows and interactive messages.

**Tasks:**

1. Update integration test fixtures for interactive messages
2. Update integration tests for check, report, contact flows
3. Update E2E tests for complete conversation flows
4. Test interactive message webhooks in integration
5. Test error handling with interactive messages
6. Run `make test-integration` and `make test-e2e`
7. Commit and create PR

**Test Coverage:**

- Test integration tests use interactive message mocks
- Test E2E tests validate complete flows with buttons/lists
- Test webhook parsing for interactive callbacks
- Test all flows (check, report, contact) work end-to-end

**Acceptance Criteria:**

- [ ] Integration tests updated for configuration-driven flows
- [ ] E2E tests validate interactive message flows
- [ ] All integration and E2E tests pass
- [ ] Coverage remains 100%
- [ ] Pre-commit checks pass

---

## Testing Strategy

### Test-Driven Development (TDD) Approach

For each issue:

1. **Write Failing Tests First**

   - Unit tests for new methods/functionality
   - Integration tests for component interactions
   - E2E tests for user flows

2. **Implement to Pass**

   - Write minimal code to make tests pass
   - Focus on single responsibility

3. **Refactor**

   - Clean up code while keeping tests green
   - Ensure ≤10 lines per function

4. **Quality Gates**
   - 100% test coverage (enforced by pytest)
   - No mypy errors (strict mode)
   - No ruff errors (linting + formatting)
   - Pre-commit hooks pass

### Test Coverage Requirements

**Maintain 100% coverage throughout migration:**

- **Unit Tests (70%)**: Test each method in isolation with mocks
- **Integration Tests (20%)**: Test component interactions
- **E2E Tests (10%)**: Test complete conversation flows

### Coverage Validation

```bash
# Run tests with coverage report
make test-cov

# View HTML report
open htmlcov/index.html

# Coverage must be ≥ 100% for all modified files
```

---

## Workflow for Each Issue

```bash
# 1. Check document for next issue
cat docs/whatsapp-interactive-messages-migration.md

# 2. Create GitHub issue (copy issue section from doc)
gh issue create --title "Issue #X: Title" --body "Description from doc"

# 3. Create branch
make issue number=X name=feature-branch-name

# 4. Write failing tests (TDD)
# Edit test files
make test-unit  # Verify tests fail

# 5. Implement code to pass tests
# Edit source files
make test-unit  # Verify tests pass

# 6. Ensure 100% coverage
make test-cov
# Check htmlcov/index.html for any gaps

# 7. Check mypy and ruff
make type-check  # No errors
make lint        # No errors
make format      # Auto-format

# 8. Run all pre-commit checks
make check  # Runs lint, type-check, all tests

# 9. Commit changes
git add -A
git commit -m "feat: implement feature

Detailed description.

Closes #X"

# 10. Create PR and check CI
make pr-issue number=X
# Wait for CI to pass

# 11. Merge and squash PR
gh pr merge --squash

# 12. Update document progress
# Mark issue as complete in this document
```

---

## Benefits Summary

### User Experience

- ✅ Native WhatsApp UI (buttons, lists) via **Meta's official API only**
- ✅ Faster input (tap vs. type)
- ✅ Reduced errors (no typos)
- ✅ Visual hierarchy (clear options)

### Configuration-Driven Architecture

- ✅ **Add new flows via YAML only** (no code changes)
- ✅ Non-developers can modify conversation flows
- ✅ Flows defined in readable, version-controlled configuration
- ✅ Validation catches errors at startup, not runtime

### Developer Experience

- ✅ Simpler state machine (11 → 5 states)
- ✅ Less text parsing (category, menu removed)
- ✅ Generic flow engine replaces hardcoded logic
- ✅ Cleaner code (~477 lines → ~300 in router, rest in config)
- ✅ Separation of concerns (flows vs. business logic)

### Maintenance & Extensibility

- ✅ **Add "Contact Us" flow in 10 minutes via config**
- ✅ Easy to extend (add categories = edit YAML)
- ✅ Better error handling (structured data)
- ✅ Improved testability (config validation + mocks)

---

## Rollback Plan

If issues arise:

1. **Issue-Level Rollback**: Revert single PR if issue detected
2. **Backward Compatibility**: Keep text parsing for critical paths during migration
3. **Feature Flags**: Can add flags to toggle interactive messages if needed

Each issue is isolated and can be reverted independently.

---

## Progress Tracking

**Milestone:** [WhatsApp Interactive Messages & Config-Driven Flows](https://github.com/barry47products/is-it-stolen/milestone/6)

| Issue | Title | Dependencies | Status | PR | Merged |
|-------|-------|--------------|--------|----|----|
| [#103](https://github.com/barry47products/is-it-stolen/issues/103) | Add Interactive Message Support (Meta API) | None | ✅ Complete | [#116](https://github.com/barry47products/is-it-stolen/pull/116) | ✅ |
| [#104](https://github.com/barry47products/is-it-stolen/issues/104) | Add Interactive Message Parsing | None | ✅ Complete | [#117](https://github.com/barry47products/is-it-stolen/pull/117) | ✅ |
| [#105](https://github.com/barry47products/is-it-stolen/issues/105) | Add Interactive Response Builder | None | ✅ Complete | [#118](https://github.com/barry47products/is-it-stolen/pull/118) | ✅ |
| [#106](https://github.com/barry47products/is-it-stolen/issues/106) | Migrate Main Menu to Reply Buttons | #103, #104, #105 | ✅ Complete | [#119](https://github.com/barry47products/is-it-stolen/pull/119) | ✅ |
| [#107](https://github.com/barry47products/is-it-stolen/issues/107) | Migrate Category Selection to Lists | #103, #104, #105 | ✅ Complete | [#120](https://github.com/barry47products/is-it-stolen/pull/120) | ✅ |
| [#108](https://github.com/barry47products/is-it-stolen/issues/108) | Create Configuration Loader | None | ✅ Complete | [#121](https://github.com/barry47products/is-it-stolen/pull/121) | ✅ |
| [#109](https://github.com/barry47products/is-it-stolen/issues/109) | Create Handler Registry | None | 🔲 Not Started | - | - |
| [#110](https://github.com/barry47products/is-it-stolen/issues/110) | Build Flow Execution Engine | #108, #109 | 🔲 Not Started | - | - |
| [#111](https://github.com/barry47products/is-it-stolen/issues/111) | Migrate Check Flow to Config | #110 | 🔲 Not Started | - | - |
| [#112](https://github.com/barry47products/is-it-stolen/issues/112) | Migrate Report Flow to Config | #111 | 🔲 Not Started | - | - |
| [#113](https://github.com/barry47products/is-it-stolen/issues/113) | Add Contact Us Flow (Config Only!) | #112 | 🔲 Not Started | - | - |
| [#114](https://github.com/barry47products/is-it-stolen/issues/114) | Simplify State Machine | #113 | 🔲 Not Started | - | - |
| [#115](https://github.com/barry47products/is-it-stolen/issues/115) | Update Integration & E2E Tests | #114 | 🔲 Not Started | - | - |

**Status Legend:**

- 🔲 Not Started
- 🔄 In Progress
- ✅ Complete
- ❌ Blocked

---

## API Compliance

**This migration uses ONLY Meta's official WhatsApp Cloud API:**

- [WhatsApp Cloud API - Overview](https://developers.facebook.com/docs/whatsapp/cloud-api/overview)
- [WhatsApp Cloud API - Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages)
- [WhatsApp Cloud API - Reply Buttons](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-reply-buttons-messages)
- [WhatsApp Cloud API - List Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-list-messages)
- [WhatsApp Cloud API - Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components)

**No third-party APIs. No unofficial libraries.** All payloads match Meta's official specifications exactly.

---

## Additional Resources

- [Project CLAUDE.md](../CLAUDE.md) - Project coding standards
- [Python Codebase Evaluation Guide](./python-codebase-evaluation-guide.md) - Code quality standards

For detailed patterns on configuration-driven flows, see the agent research output above (handler registries, flow validators, execution engines, etc.).
