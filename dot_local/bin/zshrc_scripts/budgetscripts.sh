# Aliases
alias awsbudget='aws budgets describe-budget --account-id $(aws sts get-caller-identity --query Account --output text) --budget-name "MonthlyCostBudget"'
alias awsspend='aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --query "ResultsByTime[0].Total.BlendedCost.Amount"'

# Deduplicate PATH
export PATH=$(echo "$PATH" | awk -v RS=':' '!a[$0]++' | tr '\n' ':')

# OCI Monthly Spend Function
oci_monthly_spend() {
  local START="$(date '+%Y-%m-01T00:00:00Z')"
  local NEXTMONTH="$(date -d '+1 month' +'%Y%m%d')"
  local END="$(date -d $NEXTMONTH '+%Y-%m-01T00:00:00Z')"
  local LASTARG

  if [[ $DEBUG -eq 1 ]]; then
      LASTARG="--debug"
  else
      LASTARG=''
  fi

  oci usage-api usage-summary request-summarized-usages \
    --tenant-id "$OCI_TENANTID" \
    --time-usage-started "$START" \
    --time-usage-ended "$END" \
    --granularity "MONTHLY" $LASTARG "$@"
}

# GitHub Billing Summary Function
github_billing_summary() {
  if [[ $DEBUG -eq 1 ]]; then
    echo "DEBUG is on"
  fi

  local target="$1"                 # org or username
  local is_user=1
  local output_file=""
  local raw=0

  # Argument parsing
  shift
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --user)
        is_user=1
        shift
        ;;
      --raw)
        raw=1
        shift
        ;;
      --output)
        output_file="$2"
        shift 2
        ;;
      *)
        echo "Unknown argument: $1" >&2
        return 1
        ;;
    esac
  done

  if [[ -z "$GITHUB_TOKEN" ]]; then
    echo "GITHUB_TOKEN is not set"
    return 1
  fi

  local base_url="https://api.github.com"
  local prefix="$([[ $is_user -eq 1 ]] && echo "users" || echo "orgs")/$target/settings/billing"

  local CURLFLAG
  if [[ $DEBUG -eq 1 ]]; then
    CURLFLAG="-v"
  else
    CURLFLAG="-s"
  fi

  # Fetch all three billing categories
  local actions=$(curl $CURLFLAG -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "$base_url/$prefix/actions")
  local packages=$(curl $CURLFLAG -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "$base_url/$prefix/packages")
  local storage=$(curl $CURLFLAG -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" "$base_url/$prefix/shared-storage")

  if [[ $raw -eq 1 ]]; then
    local date=$(date +%Y-%m-%d)
    local actions_csv=$(echo "$actions" | jq -r '[.total_minutes_used, .total_paid_minutes_used] | @csv')
    local packages_csv=$(echo "$packages" | jq -r '[.total_gigabytes_bandwidth_used, .total_paid_gigabytes_bandwidth_used] | @csv')
    local storage_csv=$(echo "$storage" | jq -r '[.days_left_in_billing_cycle, .estimated_paid_storage_for_month, .estimated_storage_for_month] | @csv')
    local row="$date,$actions_csv,$packages_csv,$storage_csv"

    echo "$row"

    if [[ -n "$output_file" ]]; then
      if [[ ! -f "$output_file" ]]; then
        echo "date,actions_total,actions_paid,packages_gb,packages_paid_gb,storage_days_left,storage_paid_gb_est,storage_total_gb_est" >> "$output_file"
      fi
      echo "$row" >> "$output_file"
    fi
  else
    echo "📦 GitHub Billing Summary for: $target"
    echo "--- Actions ---"
    if [[ $DEBUG -eq 1 ]]; then
      echo "$actions"
    else
      echo "$actions" | jq '{total_minutes_used, total_paid_minutes_used}'
    fi
    echo "--- Packages ---"
    if [[ $DEBUG -eq 1 ]]; then
      echo "$packages"
    else
      echo "$packages" | jq '{total_gigabytes_bandwidth_used, total_paid_gigabytes_bandwidth_used}'
    fi
    echo "--- Shared Storage ---"
    if [[ $DEBUG -eq 1 ]]; then
      echo "$storage"
    else
      echo "$storage" | jq '{days_left_in_billing_cycle, estimated_paid_storage_for_month, estimated_storage_for_month}'
    fi
  fi
}
