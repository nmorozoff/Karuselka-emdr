#!/usr/bin/env bash
# Загрузить исправленный blueprint в живой сценарий Make через REST API.
#
# Токен: Make → Profile → API → Add token (нужны права scenarios:write)
# export MAKE_API_TOKEN="ваш-токен"
#
# Использование:
#   ./patch-make-scenario.sh                          # поиск по имени сценария
#   ./patch-make-scenario.sh 12345678                 # явный scenario ID
#   MAKE_TEAM_ID=99 ./patch-make-scenario.sh

set -euo pipefail

ZONE="${MAKE_ZONE:-eu2.make.com}"
API_BASE="https://${ZONE}/api/v2"
SCENARIO_NAME="${MAKE_SCENARIO_NAME:-Выкладка каруселей Инста1 + Railway музыка (черновик)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLUEPRINT_FILE="${BLUEPRINT_FILE:-${SCRIPT_DIR}/vykladka-karusely-inst1-fixed.blueprint.json}"

if [[ -z "${MAKE_API_TOKEN:-}" ]]; then
  echo "Ошибка: задайте MAKE_API_TOKEN (Make → Profile → API)." >&2
  exit 1
fi

if [[ ! -f "${BLUEPRINT_FILE}" ]]; then
  echo "Ошибка: файл blueprint не найден: ${BLUEPRINT_FILE}" >&2
  exit 1
fi

auth_header() {
  printf 'Authorization: Token %s' "${MAKE_API_TOKEN}"
}

json_get() {
  python3 - "$@" <<'PY'
import json, sys
data = json.load(sys.stdin)
path = sys.argv[1:]
cur = data
for key in path:
    if isinstance(cur, list):
        cur = cur[int(key)]
    else:
        cur = cur[key]
print(cur)
PY
}

find_team_id() {
  if [[ -n "${MAKE_TEAM_ID:-}" ]]; then
    echo "${MAKE_TEAM_ID}"
    return
  fi
  local org_id teams
  org_id="$(curl -fsS -H "$(auth_header)" -H "Accept: application/json" "${API_BASE}/organizations" \
    | json_get organizations 0 id)"
  teams="$(curl -fsS -G -H "$(auth_header)" -H "Accept: application/json" \
    --data-urlencode "organizationId=${org_id}" \
    "${API_BASE}/teams")"
  printf '%s' "${teams}" | json_get teams 0 id
}

find_scenario_id() {
  local team_id="$1" scenario_arg="${2:-}"
  if [[ -n "${scenario_arg}" ]]; then
    echo "${scenario_arg}"
    return
  fi
  local scenarios
  scenarios="$(curl -fsS -G -H "$(auth_header)" -H "Accept: application/json" \
    --data-urlencode "teamId=${team_id}" \
    --data-urlencode "pg[limit]=100" \
    "${API_BASE}/scenarios")"
  python3 - "${SCENARIO_NAME}" <<'PY' <<<"${scenarios}"
import json, sys
name = sys.argv[1]
data = json.load(sys.stdin)
for item in data.get("scenarios", []):
    if item.get("name") == name:
        print(item["id"])
        break
else:
    sys.exit(2)
PY
}

TEAM_ID="$(find_team_id)"
echo "Team ID: ${TEAM_ID}"

SCENARIO_ID="$(find_scenario_id "${TEAM_ID}" "${1:-}")" || {
  echo "Сценарий «${SCENARIO_NAME}» не найден. Передайте ID аргументом: $0 <scenarioId>" >&2
  exit 1
}
echo "Scenario ID: ${SCENARIO_ID}"

CURRENT="$(curl -fsS -H "$(auth_header)" -H "Accept: application/json" \
  "${API_BASE}/scenarios/${SCENARIO_ID}")"

SCHEDULING="$(printf '%s' "${CURRENT}" | json_get scenario scheduling 2>/dev/null || echo '{"type":"indefinitely","interval":900}')"

BODY="$(python3 - "${BLUEPRINT_FILE}" "${SCHEDULING}" <<'PY'
import json, pathlib, sys
blueprint_path = pathlib.Path(sys.argv[1])
scheduling_raw = sys.argv[2]
blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
try:
    scheduling = json.loads(scheduling_raw) if scheduling_raw else {"type": "indefinitely", "interval": 900}
except json.JSONDecodeError:
    scheduling = {"type": "indefinitely", "interval": 900}
payload = {
    "blueprint": json.dumps(blueprint, ensure_ascii=False),
    "scheduling": json.dumps(scheduling, ensure_ascii=False),
}
print(json.dumps(payload, ensure_ascii=False))
PY
)"

echo "PATCH ${API_BASE}/scenarios/${SCENARIO_ID} ..."
RESPONSE="$(curl -fsS -X PATCH \
  -H "$(auth_header)" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  --data "${BODY}" \
  "${API_BASE}/scenarios/${SCENARIO_ID}?confirmed=true")"

echo "Готово. Сценарий обновлён:"
printf '%s' "${RESPONSE}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('scenario',{}).get('name',''), 'id=', d.get('scenario',{}).get('id',''))"
