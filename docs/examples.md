# Requirement analysis examples

These hand-written examples specify the intended behavior of the planned checks. They illustrate ambiguous wording, measurable requirements, and potential false positives. They are not an evaluation dataset or measured results.

The current `RL001` rule covers E01 and E02 and skips the double-quoted label in E08. The token-based `RL002` rule covers E03. `RL003` covers selected performance phrases, including E04. See the README for supported phrases and limitations.

## Initial warning categories

| Category                     | What it means                                        | What the tool should ask for                   |
| ---------------------------- | ---------------------------------------------------- | ---------------------------------------------- |
| Vague wording                | A subjective description such as "user-friendly"     | An observable outcome or acceptance test       |
| Imprecise quantity           | A quantity such as "many" with no clear amount       | A count, range, or other explicit limit        |
| Missing performance criteria | A performance claim without enough measurable detail | A metric, target, and relevant test conditions |

## Examples and expected results

| ID  | Requirement                                                                            | Expected review finding                                                                                                                 |
| --- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| E01 | The application should load quickly.                                                   | Highlight "quickly" as vague wording. Ask for a loading-time target and test conditions.                                                |
| E02 | The interface must be user-friendly.                                                   | Highlight "user-friendly". Ask which task users must complete and how success will be assessed.                                         |
| E03 | The application should support many users.                                             | Highlight "many" as an imprecise quantity. Ask how many users and whether they are concurrent.                                          |
| E04 | The system should process requests with low latency.                                   | Flag the missing latency target and workload conditions.                                                                                |
| E05 | Under workload W1, at least 95% of dashboard loads must finish within 2 seconds.       | No warning from the initial wording checks. A reviewer must still verify that W1 is defined and the target is appropriate.              |
| E06 | The system must support 100 concurrent users under workload W1.                        | No imprecise-quantity warning. Other acceptance criteria may still be needed.                                                           |
| E07 | When the user selects Cancel, the system must close the dialog without saving changes. | No warning from the initial checks. An observable behavior can be testable without a numeric target.                                    |
| E08 | The system must display the label "Quickly" on the shortcut button.                    | No vague-wording warning is intended for the quoted label. This case tests a potential false positive in keyword matching. |

`RL003` does not repeat the `quickly` finding handled by `RL001`.

## Performance guidance

| Requirement | Expected performance finding |
| --- | --- |
| The page should load fast. | Ask for a loading-time limit and test conditions. |
| Latency should be very low. | Ask for a latency limit and workload conditions. |
| The app must perform under lower latencies. | Ask for a latency limit, just as for low latency. |
| The app must perform under lower latency. | Ask for a latency limit. |
| The app must perform under low latencies. | Ask for a latency limit. |
| Latencies must be lower than 100 ms. | No missing-time-limit finding from RL003. |
| The page must load within 2 seconds for 100 concurrent users. | None from RL003. |
| The page should load fast for 100 concurrent users. | The user count does not define a time limit. |
| The system must display the label "load fast". | None for the quoted label. |
| Selecting the Fast preset must change the preview resolution. | None from RL003. |

These are rule expectations, not measured classifier results. A classifier flag can still request review when a rule finds nothing.

## Example suggestion

For E01: "Specify the maximum loading time and the conditions under which it will be tested."

An illustrative rewrite is: "Under workload W1, at least 95% of dashboard loads must finish within 2 seconds." The numbers and workload name are examples, not targets that RequirementLint should choose automatically.
