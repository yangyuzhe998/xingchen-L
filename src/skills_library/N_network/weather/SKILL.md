---
name: weather
description: Get current weather information for a specific location using curl and wttr.in.
---

# Weather Skill

Use this skill to check the weather for any location.

## Usage

To get the weather for a city, execute the following command in the shell:

```bash
curl -s "wttr.in/{City}?format=3"
```

### Parameters
- `{City}`: The name of the city (e.g., Beijing, London, New_York). Use `+` or `_` for spaces.

### Examples

Check weather in Beijing:
```bash
curl -s "wttr.in/Beijing?format=3"
```

Check weather in New York:
```bash
curl -s "wttr.in/New_York?format=3"
```
