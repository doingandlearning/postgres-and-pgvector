| Field Name          | Example Value                                                                  | Why It’s Useful                                                        |
| ------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| `doc_title`         | `"Final Acts - Geneva 1984"`                                                   | If you’re loading multiple ITU documents.                              |
| `chunk_id`          | `"article_4_p3"`                                                               | Unique ID for referencing chunks in search or citations.               |
| `section_type`      | `"Article"` or `"Annex"` or `"Resolution"`                                     | Enables filtering search results (e.g. only show procedural rules).    |
| `section_number`    | `"4"`                                                                          | Useful for user-facing citations.                                      |
| `section_title`     | `"Procedure Concerning Modifications to the Plan"`                             | For display in UI or summarisation.                                    |
| `page_start`        | `12`                                                                           | Helps map back to original PDF for legal traceability.                 |
| `page_end`          | `14`                                                                           | Same as above.                                                         |
| `tokens`            | `512`                                                                          | Helpful for context window management.                                 |
| `text_language`     | `"English"`                                                                    | Geneva acts exist in several languages.                                |
| `keywords`          | `[ "frequency assignment", "modification procedure", "IFRB", "coordination" ]` | Improves semantic search relevance.                                    |
| `entities`          | `[ "ITU", "IFRB", "Geneva", "Libya" ]`                                         | For entity-based queries.                                              |
| `mentions_articles` | `[ "Article 5", "Annex 3" ]`                                                   | Helps trace cross-references (e.g. when chunks cite other sections).   |
| `contains_table`    | `true`                                                                         | Enables chunk-specific handling in UI or retrieval (tables vs. prose). |
| `contains_figure`   | `true`                                                                         | Same as above.                                                         |
| `interference_type` | `"A1"`                                                                         | If chunk describes a specific interference case.                       |
| `service_type`      | `"Aeronautical Radionavigation"`                                               | E.g. radio vs. aeronautical context.                                   |
| `propagation_type`  | `"Warm sea"`                                                                   | From Annex 2 propagation sections.                                     |
| `country_mentions`  | `[ "France", "Libya", "Kenya" ]`                                               | Enables country-specific retrieval or analytics.                       |
| `version`           | `"1984"`                                                                       | Useful if you store future amendments or revised plans.                |
