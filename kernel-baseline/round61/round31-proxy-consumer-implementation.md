# AI2-ROUND31 — Stage A proxy consumer port: implementation record

Base: `8ad08f75ddf056e1ee600e1339e0463c5fcbdc9a` (`android17-6.18.33_r00`)
Branch: `ai-parallel/stagea-port-until-boot`
Scope: port the Qualcomm boot time regulator proxy consumer helper to ACK 6.18.33,
validate its lifecycle, and establish whether the HOS4.3 PM8150 L5/L9 proxy
requests can be expressed on the ACK PMIC topology.

## 1. Input identity and what could not be obtained

| Input | Status |
|---|---|
| ACK source | local `common` at `8ad08f75`, clean (`git status` empty) |
| KONA `cad09e061ef6cf689a4a1e54d27562e0f042236a` | NOT OBTAINABLE here |
| `drivers/regulator/proxy-consumer.c` in ACK HEAD | ABSENT (whole-tree grep, Kconfig, Makefile, bindings, DTS: 0 hits) |
| Same file in mainline v6.1/v6.6/v6.12/master | ABSENT (404 on aosp-mirror/kernel_common) |

`cad09e06` could not be fetched: `android.googlesource.com` is unreachable from
this host (proxy CONNECT 502), and `aosp-mirror/kernel_msm` has neither that
commit nor a `kona` branch. The semantic reference actually used is the same
Qualcomm implementation as it exists in this very ACK repository:

- `653a867e09b6` "ANDROID: GKI: regulator: Add proxy consumer driver"
  (cherry-picked from kernel/msm `cf03466c074e912a8aa3e079e1b7ea1cc17b18ba`)
- `4bad67ba2a51` "Call proxy-consumer functions for each regulator registered"
  (from kernel/msm `ff753edc6d60e1e1043931409e6d3ac6e01b8108`)

Both are reachable only from `aosp/deprecated/android-4.19`; they are **not**
ancestors of HEAD, which is why the tree never carried the feature. Their
content was extracted with `git show` and used as the authoritative semantics.

Cross-check: the same file on a contemporary Qualcomm product kernel
(`android-msm-barbet-4.19-android12L`) differs only by the later `sync_state`
extension (`no_sync_state`, conditional list_add, unconditional remove on
unregister). ACK's `qcom-rpmh-regulator.c` has **no** `sync_state` callback
(`grep -c sync_state` = 0) and ACK's core has no `regulator_sync_state()`, so
the `sync_state` variant is not applicable and was deliberately not ported.

## 2. Topology verification (the ROUND13 "self reference" question)

ROUND13 records, at group level, `proxy-supply` pointing at the group's own
child; and at child level, `qcom,proxy-consumer-enable` plus
`qcom,proxy-consumer-current = 100000`.

That is not a self reference defect. The Qualcomm core hook is:

```c
rdev->proxy_consumer = regulator_proxy_consumer_register(dev, config->of_node);
```

- `dev` is the *registering* device, i.e. the provider group device. Its
  `of_node` is the group node, so `regulator_get(dev, "proxy")` resolves
  `proxy-supply` **on the group node**.
- `config->of_node` is the regulator child, so `qcom,proxy-consumer-*` is read
  **on the child node**.

The split therefore matches ROUND13 exactly. Resolution chain in ACK 6.18.33:

1. `regulator_get()` -> `_regulator_get_common()` -> `regulator_dev_lookup()`
2. `regulator_dt_lookup()` -> `of_regulator_dev_lookup(dev, dev_of_node(dev), "proxy")`
3. `of_get_regulator()` -> `of_parse_phandle(np, "proxy-supply", 0)` (group node)
4. `of_find_regulator_by_node()` -> `class_find_device_by_of_node(&regulator_class, np)`

Step 4 succeeds because the hook runs after `device_add(&rdev->dev)` in
`regulator_register()`. No recursion, no phandle rewrite, and no second supply
is invented.

## 3. Implementation

New files:

- `drivers/regulator/proxy-consumer.c`
- `include/linux/regulator/proxy-consumer.h`

Modified:

- `drivers/regulator/Kconfig` — `CONFIG_REGULATOR_PROXY_CONSUMER` (bool)
- `drivers/regulator/Makefile` — appended after `userspace-consumer.o`, i.e.
  after `core.o`, so that the proxy `late_initcall_sync` still runs after the
  regulator core's own `late_initcall_sync`
- `include/linux/regulator/driver.h` — `ANDROID_KABI_USE(1, struct proxy_consumer *proxy_consumer)`
  in place of the existing `ANDROID_KABI_RESERVE(1)`, plus the header include
- `drivers/regulator/core.c` — register and unregister hooks
- `Documentation/devicetree/bindings/regulator/qcom,rpmh-regulator.yaml`
- `arch/arm64/configs/dby_w09_storage_first.fragment`

Deviations from the 4.19 original, each deliberate:

1. `regulator_proxy_consumer_unregister()` takes `struct regulator_dev *`
   instead of `struct proxy_consumer *`. The consumer stores a back-pointer and
   the bulk removal clears `rdev->proxy_consumer` before freeing, so a
   late_initcall_sync removal followed by a regulator teardown cannot leave a
   dangling pointer that the unregister path would compare against.
2. `qcom,proxy-consumer-current` is rejected when it exceeds `INT_MAX`
   (`regulator_set_load()` takes `int`). The 4.19 original silently truncated a
   `u32` into a negative load.
3. `qcom,proxy-consumer-enable` must be an empty property. `of_property_read_bool()`
   accepts any present property, including `= <1>`; the length is now checked so
   a type error is rejected in the driver as well as in the schema.
4. An inverted or over-`INT_MAX` voltage pair is rejected instead of being
   silently skipped.
5. A node that carries proxy properties but expresses no request at all
   (enable absent, current 0, no voltage) is rejected instead of registering a
   consumer that would do nothing.

Build-discovered defect: a local variable named `current` collides with the
kernel `current` macro (`get_current()`), producing
`-Werror,-Wstrict-prototypes` plus `conflicting types for 'get_current'`. Renamed
to `current_ua`.

## 4. Lifecycle, as actually exercised

The bulk path is `late_initcall_sync(regulator_proxy_consumer_remove_all)`:
it sets `proxy_consumers_removed`, clears each `rdev->proxy_consumer`, then
disables, zeroes the load, restores voltage and puts, in that order.

A single regulator teardown goes through `regulator_unregister()`, which calls
`regulator_proxy_consumer_unregister(rdev)` **before** taking
`regulator_list_mutex`, so the lock order is always
`proxy_consumer_list_mutex` -> `regulator_list_mutex` on both paths and there is
no ABBA with the core.

Register path lock order is the same: the helper holds
`proxy_consumer_list_mutex` while calling `regulator_get()`, which internally
takes `regulator_list_mutex`.

Failure unwinding is reverse-order and label-based: enable failure drops the
load vote, load failure drops the voltage, and every path puts the regulator
exactly once.

## 5. Difference in the ACK core that changes the observable outcome

In 4.19, `regulator_init_complete()` runs synchronously inside
`late_initcall_sync` and disables unused regulators right there. In ACK 6.18.33
it only schedules `regulator_init_complete_work` with a 30 second delay
(`msecs_to_jiffies(30000)`), and the actual `regulator_late_cleanup()` runs from
that work item.

Consequence: the proxy vote is withdrawn at `late_initcall_sync`, and if no real
consumer has enabled the rail by the time the delayed work runs, the core will
disable it. That is upstream behaviour applied to every regulator, not something
this port introduces, but it means "proxy withdrawn" no longer implies "rail
stays up until a consumer arrives". Recorded, not worked around.

## 6. Verdict on the HOS4.3 L5/L9 requests

`qcom_rpmh_regulator_probe()` binds **one** platform device per PMIC and passes
that same `dev` to `devm_regulator_register()` for every child:

```c
struct device *dev = &pdev->dev;
...
vreg->dev = dev;
reg_config.dev = dev;
rdev = devm_regulator_register(dev, &vreg->rdesc, &reg_config);
```

Therefore `regulator_get(dev, "proxy")` reads a single `proxy-supply` property
from the PMIC group node. One PMIC group can hold exactly one `proxy-supply`.

HOS4.3 has one provider group per ARC resource (`rpmh-regulator-ldoa5`,
`rpmh-regulator-ldoa9`), so L5 and L9 each get their own group and their own
`proxy-supply`. ACK collapses all PM8150 rails into one
`qcom,pm8150-rpmh-regulators` node, so it can serve only one of the two.

This is a topology limitation, not an implementation defect, and it is why no
board DTS property was added in this round: wiring `proxy-supply` to L5 would
silently make L9's request resolve the same phandle, i.e. L9 would vote on L5.
The schema accepts that arrangement (`round31-proxy-two-child-same-group.dts`
validates clean), which is precisely why it must not be shipped.

The Kconfig symbol is nonetheless enabled for `dby_w09`, so the helper is really
compiled and linked; it simply has no node to attach to until the topology
question is resolved.

## 7. Verification actually run this round

| Check | Result |
|---|---|
| `git apply --check` / apply / `git diff --check`, 12 patches | 12/12, all rc=0 |
| `checkpatch.pl --strict` on the 3 new patches | 0 errors, 0 checks; 1 warning (new-file/MAINTAINERS hint) |
| `dt_binding_check`, dtschema 2023.9 and 2026.9, forced rebuild | rc=0 both |
| `dt-doc-validate` both versions | rc=0, empty output |
| Binding fixtures, 6 cases x 2 versions + dtc phandle case | 13/13 assertions PASS |
| Executable lifecycle test (real source, mocked kernel API) | 38 checks, 0 failures |
| Kleaf `//common:dby_w09` | see report |

## 8. What is still open

- L5/L9 proxy topology on ACK: blocked on the single-group model. Resolving it
  needs either per-resource provider devices (the ARC provider that ROUND31 is
  explicitly not allowed to implement) or a split PMIC node layout, neither of
  which is a "port" of the KONA semantics.
- No runtime validation. Nothing here proves the rails reach their HOS4.3 state
  on hardware.
- `qcom,proxy-consumer-voltage` is implemented and schema-checked but has no
  HOS4.3 user for L5/L9 (ROUND13 records only enable + current).
