/* ROUND32 executable lifecycle test for drivers/regulator/proxy-consumer.c
 *
 * The real driver source is compiled into this harness through the mock tree
 * in tests/mock, so the assertions below exercise the shipped code rather
 * than a reimplementation of it.
 *
 * Focus: child-scoped proxy-supply mapping.  Two children of one flattened
 * PM8150 provider device (l5, l9) each target their own regulator, vote
 * independently, and are withdrawn without affecting each other.
 */
#include <mock_core.h>

struct mock_stats mock;
int (*mock_late_initcall_fn)(void);
int (*mock_late_initcall_retry_fn)(void);

#include <drivers/regulator/proxy-consumer.c>

static int failures;
static int checks;

#define CHECK(cond, msg)						\
	do {								\
		checks++;						\
		if (cond) {						\
			printf("ok   %s\n", msg);			\
		} else {						\
			printf("FAIL %s  (%s:%d)\n", msg, __FILE__, __LINE__); \
			failures++;					\
		}							\
	} while (0)

static void reset_mock(void)
{
	memset(&mock, 0, sizeof(mock));
	mock_unregister_all_targets();
	/* proxy_consumers_removed is a file-static of the driver under test;
	 * this harness compiles the driver into the same TU, so reset it
	 * alongside the mock counters.
	 */
	proxy_consumers_removed = false;
}

static void add_flag(struct device_node *np, const char *name)
{
	np->props[np->nprops].name = name;
	np->props[np->nprops].length = 0;
	np->props[np->nprops].value = NULL;
	np->nprops++;
}

static void add_u32(struct device_node *np, const char *name, u32 v)
{
	u32 *cell = malloc(4);

	*cell = v;
	np->props[np->nprops].name = name;
	np->props[np->nprops].length = 4;
	np->props[np->nprops].value = cell;
	np->nprops++;
}

static void add_u32_pair(struct device_node *np, const char *name, u32 a, u32 b)
{
	u32 *cells = malloc(8);

	cells[0] = a;
	cells[1] = b;
	np->props[np->nprops].name = name;
	np->props[np->nprops].length = 8;
	np->props[np->nprops].value = cells;
	np->nprops++;
}

/* supply phandles carry borrowed pointers (length 8, not owned). */
static void add_supply(struct device_node *np, const char *name, void *target)
{
	np->props[np->nprops].name = name;
	np->props[np->nprops].length = sizeof(void *);
	np->props[np->nprops].value = target;
	np->nprops++;
}

/* only owned u32/u32-pair allocations are freed; supply phandle values are
 * borrowed node pointers and are left alone.
 */
static void del_props(struct device_node *np)
{
	int i;

	for (i = 0; i < np->nprops; i++)
		if (np->props[i].length == 4 && np->props[i].value)
			free((void *)np->props[i].value);
	np->nprops = 0;
}

/* fixture nodes */
static struct device_node l5_node = { .full_name = "/pm8150-regulators/ldo5" };
static struct device_node l9_node = { .full_name = "/pm8150-regulators/ldo9" };
static struct device_node ghost_node = { .full_name = "/pm8150-regulators/ghost" };
static struct device_node container_node = { .full_name = "/pm8150-regulators" };

static void clear_nodes(void)
{
	del_props(&l5_node);
	del_props(&l9_node);
	del_props(&ghost_node);
	del_props(&container_node);
}

static int votes_load_val(void *target)
{
	int i;

	for (i = mock.nvotes - 1; i >= 0; i--)
		if (mock.votes[i].target == target &&
		    mock.votes[i].action == MOCK_LOAD)
			return mock.votes[i].value;
	return -1;
}

/* standard child-scoped self-target props for one child */
static void add_self_target_props(struct device_node *np)
{
	add_supply(np, "proxy-supply", np);
	add_flag(np, "qcom,proxy-consumer-enable");
	add_u32(np, "qcom,proxy-consumer-current", 100000);
}

int main(void)
{
	struct device group = { .name = "pm8150-regulators",
				.of_node = &container_node };
	struct regulator_dev rdev5 = { 0 };
	struct regulator_dev rdev9 = { 0 };
	struct proxy_consumer *c;

	printf("== ROUND32 child-scoped proxy consumer lifecycle test ==\n");

	/* 1. plain regulator without proxy properties: behavior unchanged */
	clear_nodes();
	reset_mock();
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(c == NULL, "plain child without proxy props -> NULL");
	CHECK(mock.get_calls == 0, "plain child -> no regulator lookup");
	CHECK(rdev5.proxy_consumer == NULL, "plain child -> rdev untouched");

	/* 2. child-scoped self-targets: L5 and L9 each vote only on
	 *    their own regulator (the ROUND32 core scenario)
	 */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	mock_register_target(&l9_node, &rdev9);
	add_self_target_props(&l5_node);
	add_self_target_props(&l9_node);

	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	rdev9.proxy_consumer = regulator_proxy_consumer_register(&group, &l9_node, &rdev9);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer), "l5 child-scoped consumer registered");
	CHECK(!IS_ERR_OR_NULL(rdev9.proxy_consumer), "l9 child-scoped consumer registered");
	CHECK(mock.get_calls == 2, "exactly one lookup per child");
	CHECK(mock_count(&l5_node, MOCK_GET_OK) == 1,
	      "l5 resolved via its own node phandle");
	CHECK(mock_count(&l9_node, MOCK_GET_OK) == 1,
	      "l9 resolved via its own node phandle");
	CHECK(mock_count(&l5_node, MOCK_LOAD) == 1 && votes_load_val(&l5_node) == 100000,
	      "l5 target carries exactly one 100000 uA load vote");
	CHECK(mock_count(&l9_node, MOCK_LOAD) == 1 && votes_load_val(&l9_node) == 100000,
	      "l9 target carries exactly one 100000 uA load vote");
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 1 && mock_count(&l9_node, MOCK_ENABLE) == 1,
	      "each target enabled exactly once");
	CHECK(mock_count(&l5_node, MOCK_DISABLE) == 0 && mock_count(&l9_node, MOCK_DISABLE) == 0,
	      "no cross-disable before teardown");

	/* 3. individual unregister withdraws only its own votes */
	{
		int bal = mock.enable_balance;

		regulator_proxy_consumer_unregister(&rdev5);
		CHECK(rdev5.proxy_consumer == NULL,
		      "l5 unregister clears back-pointer");
		CHECK(mock_count(&l5_node, MOCK_DISABLE) == 1,
		      "l5 disable happened exactly once");
		CHECK(mock_count(&l5_node, MOCK_PUT) == 1, "l5 handle put once");
		CHECK(votes_load_val(&l5_node) == 0, "l5 load vote withdrawn");
		CHECK(mock_count(&l9_node, MOCK_DISABLE) == 0,
		      "l9 not disabled by l5 unregister");
		CHECK(mock_count(&l9_node, MOCK_PUT) == 0, "l9 handle untouched");
		CHECK(mock.enable_balance == bal - 1,
		      "global enable balance drops by exactly one");
	}

	/* 4. second individual unregister is a no-op (no double-disable) */
	regulator_proxy_consumer_unregister(&rdev5);
	CHECK(mock_count(&l5_node, MOCK_DISABLE) == 1,
	      "double unregister: no second disable");
	CHECK(mock_count(&l5_node, MOCK_PUT) == 1,
	      "double unregister: no second put");

	/* 5. bulk late_initcall_sync removes the surviving rail once */
	CHECK(mock_late_initcall_fn != NULL, "late_initcall_sync hook captured");
	mock_late_initcall_fn();
	CHECK(mock_count(&l9_node, MOCK_DISABLE) == 1,
	      "bulk revoke disables l9 once");
	CHECK(mock_count(&l9_node, MOCK_PUT) == 1, "bulk revoke puts l9 once");
	CHECK(mock.enable_balance == 0, "bulk revoke balance 0");
	CHECK(rdev9.proxy_consumer == NULL, "bulk revoke clears back-pointer");
	mock_late_initcall_fn();
	CHECK(mock_count(&l9_node, MOCK_DISABLE) == 1 && mock_count(&l9_node, MOCK_PUT) == 1,
	      "repeat bulk revoke is a no-op");

	/* 6. registration after the bulk removal is refused */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	add_self_target_props(&l5_node);
	mock_late_initcall_fn();
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -1, "child-scoped after revoke -> -EPERM");
	CHECK(mock.get_calls == 0, "refused registration does not look up");

	/* 7. deferred target: parked without voting, retried at
	 *    late_initcall before the bulk revoke
	 */
	clear_nodes();
	reset_mock();
	add_self_target_props(&l5_node);
	/* target not registered yet on purpose */
	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer),
	      "deferred target -> consumer parked, not an error");
	CHECK(rdev5.proxy_consumer->deferred == true, "consumer marked deferred");
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 0 && mock_count(&l5_node, MOCK_LOAD) == 0,
	      "deferred consumer made no votes");
	CHECK(mock_count(&l5_node, MOCK_GET_DEFER) == 1,
	      "lookup returned -EPROBE_DEFER");
	CHECK(mock.enable_balance == 0, "deferred consumer holds no enable");

	CHECK(mock_late_initcall_retry_fn != NULL, "late_initcall retry hook captured");
	mock_late_initcall_retry_fn();
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 0,
	      "retry with target still absent keeps no votes");
	CHECK(rdev5.proxy_consumer->deferred == true,
	      "retry leaves the consumer parked");

	/* target appears, retry applies the votes */
	mock_register_target(&l5_node, &rdev5);
	mock_late_initcall_retry_fn();
	CHECK(rdev5.proxy_consumer->deferred == false, "retry clears deferred flag");
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 1, "retry enables exactly once");
	CHECK(mock_count(&l5_node, MOCK_LOAD) == 1 && votes_load_val(&l5_node) == 100000,
	      "retry applies the 100000 uA load vote");

	/* bulk revoke then withdraws the retried votes */
	mock_late_initcall_fn();
	CHECK(mock_count(&l5_node, MOCK_DISABLE) == 1 && mock_count(&l5_node, MOCK_PUT) == 1,
	      "bulk revoke withdraws the retried consumer once");
	CHECK(rdev5.proxy_consumer == NULL, "bulk revoke clears retried back-pointer");

	/* 8. target that never registers is dropped at bulk revoke
	 *    without ever voting
	 */
	clear_nodes();
	reset_mock();
	add_supply(&l9_node, "proxy-supply", &ghost_node);
	add_flag(&l9_node, "qcom,proxy-consumer-enable");
	add_u32(&l9_node, "qcom,proxy-consumer-current", 100000);
	rdev9.proxy_consumer = regulator_proxy_consumer_register(&group, &l9_node, &rdev9);
	CHECK(!IS_ERR_OR_NULL(rdev9.proxy_consumer),
	      "ghost target -> consumer parked");
	mock_late_initcall_retry_fn();
	CHECK(rdev9.proxy_consumer->deferred == true,
	      "retry cannot resolve ghost target");
	{
		int d0 = mock.disable_calls;
		int p0 = mock.put_calls;

		mock_late_initcall_fn();
		CHECK(rdev9.proxy_consumer == NULL,
		      "bulk revoke drops the ghost consumer");
		CHECK(mock.disable_calls - d0 == 0 && mock.put_calls - p0 == 0,
		      "ghost consumer never voted, never put a handle");
	}

	/* 9. individual unregister of a parked consumer is safe */
	clear_nodes();
	reset_mock();
	add_supply(&l9_node, "proxy-supply", &ghost_node);
	add_flag(&l9_node, "qcom,proxy-consumer-enable");
	add_u32(&l9_node, "qcom,proxy-consumer-current", 100000);
	rdev9.proxy_consumer = regulator_proxy_consumer_register(&group, &l9_node, &rdev9);
	{
		int d0 = mock.disable_calls;
		int p0 = mock.put_calls;

		regulator_proxy_consumer_unregister(&rdev9);
		CHECK(mock.disable_calls - d0 == 0 && mock.put_calls - p0 == 0,
		      "unregistering a parked consumer does not touch regulators");
		CHECK(rdev9.proxy_consumer == NULL, "parked consumer freed");
	}

	/* 10. child + group double declaration is rejected with -EINVAL */
	clear_nodes();
	reset_mock();
	add_supply(&container_node, "proxy-supply", &l5_node);
	add_self_target_props(&l5_node);
	mock_register_target(&l5_node, &rdev5);
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22,
	      "group+child proxy-supply mix -> -EINVAL");
	CHECK(mock.get_calls == 0, "ambiguity rejected before any lookup");
	CHECK(rdev5.proxy_consumer == NULL, "ambiguity leaves rdev untouched");

	/* 11. legacy group-level declaration still works unchanged */
	clear_nodes();
	reset_mock();
	add_supply(&container_node, "proxy-supply", &l5_node);
	add_flag(&l5_node, "qcom,proxy-consumer-enable");
	add_u32(&l5_node, "qcom,proxy-consumer-current", 100000);
	mock_register_target(&l5_node, &rdev5);
	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer),
	      "legacy group-level consumer registered");
	CHECK(mock.last_get_id_is_proxy == 1,
	      "legacy lookup used regulator_get(\"proxy\")");
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 1 &&
	      mock_count(&l5_node, MOCK_LOAD) == 1,
	      "legacy votes applied through the group-level self-target handle");
	regulator_proxy_consumer_unregister(&rdev5);
	CHECK(mock_count(&l5_node, MOCK_DISABLE) == 1,
	      "legacy unregister disables its self-target once");

	/* 12. parse errors are still rejected before any regulator lookup */
	clear_nodes();
	reset_mock();
	add_supply(&l5_node, "proxy-supply", &l5_node);
	add_u32(&l5_node, "qcom,proxy-consumer-current", 0x80000000u);
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "current > INT_MAX -> -EINVAL");
	CHECK(mock.get_calls == 0, "rejected before lookup (child-scoped)");

	del_props(&l5_node);
	add_u32(&l5_node, "qcom,proxy-consumer-enable", 1);
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "non-empty enable flag -> -EINVAL");

	del_props(&l5_node);
	add_u32_pair(&l5_node, "qcom,proxy-consumer-voltage", 1200000, 900000);
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "inverted voltage range -> -EINVAL");

	del_props(&l5_node);
	add_u32(&l5_node, "qcom,proxy-consumer-current", 0);
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "zero-only request -> -EINVAL");
	CHECK(mock.get_calls == 0, "zero-only request never looked up");

	/* 13. vote application failures unwind in reverse order
	 *     (child-scoped)
	 */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	add_self_target_props(&l5_node);
	mock.fail_set_load = -5;
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -5, "set_load failure propagates");
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 0, "set_load failure -> no enable");
	CHECK(mock_count(&l5_node, MOCK_PUT) == 1,
	      "set_load failure -> handle put once");
	CHECK(rdev5.proxy_consumer == NULL, "failed registration leaves rdev clean");

	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	mock.fail_enable = -6;
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -6, "enable failure propagates");
	CHECK(mock_count(&l5_node, MOCK_LOAD) == 2 && votes_load_val(&l5_node) == 0,
	      "enable failure withdrew the load vote");
	CHECK(mock_count(&l5_node, MOCK_PUT) == 1, "enable failure -> handle put once");
	CHECK(rdev5.proxy_consumer == NULL, "enable failure leaves rdev clean");

	/* 14. retry vote-application failure frees the consumer cleanly */
	clear_nodes();
	reset_mock();
	add_self_target_props(&l5_node);
	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer), "parked consumer waiting for target");
	mock_register_target(&l5_node, &rdev5);
	mock.fail_set_load = -7;
	mock_late_initcall_retry_fn();
	CHECK(mock_count(&l5_node, MOCK_ENABLE) == 0,
	      "retry vote failure does not enable");
	CHECK(rdev5.proxy_consumer == NULL,
	      "failed retry frees the consumer (back-pointer cleared)");
	mock.fail_set_load = 0;

	/* 15. legacy -EPERM after bulk revoke */
	clear_nodes();
	reset_mock();
	add_flag(&l5_node, "qcom,proxy-consumer-enable");
	mock_late_initcall_fn();
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -1, "legacy after revoke -> -EPERM");

	/* 16. child-scoped cross-target phandle is rejected before lookup. */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	mock_register_target(&l9_node, &rdev9);
	add_supply(&l5_node, "proxy-supply", &l9_node);
	add_flag(&l5_node, "qcom,proxy-consumer-enable");
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22,
	      "child-scoped cross-target rejected with -EINVAL");
	CHECK(mock.get_calls == 0,
	      "child-scoped cross-target rejected before regulator lookup");
	CHECK(rdev5.proxy_consumer == NULL,
	      "child-scoped cross-target leaves owner back-pointer empty");

	/* 17. legacy group mapping also rejects a different target child. */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	mock_register_target(&l9_node, &rdev9);
	add_supply(&container_node, "proxy-supply", &l9_node);
	add_flag(&l5_node, "qcom,proxy-consumer-enable");
	c = regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22,
	      "legacy group cross-target rejected with -EINVAL");
	CHECK(mock.get_calls == 0,
	      "legacy group cross-target rejected before regulator lookup");
	CHECK(rdev5.proxy_consumer == NULL,
	      "legacy group cross-target leaves owner back-pointer empty");

	/* 18. legacy self-target remains supported and resolves to its owner. */
	clear_nodes();
	reset_mock();
	mock_register_target(&l5_node, &rdev5);
	add_supply(&container_node, "proxy-supply", &l5_node);
	add_flag(&l5_node, "qcom,proxy-consumer-enable");
	rdev5.proxy_consumer =
		regulator_proxy_consumer_register(&group, &l5_node, &rdev5);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer),
	      "legacy group self-target still registers");
	CHECK(mock_count(&l5_node, MOCK_GET_OK) == 1,
	      "legacy group self-target resolves the owner node");
	regulator_proxy_consumer_unregister(&rdev5);
	CHECK(mock_count(&l5_node, MOCK_DISABLE) == 1 &&
	      mock_count(&l5_node, MOCK_PUT) == 1,
	      "legacy self-target owner teardown withdraws once");

	clear_nodes();

	printf("\nchecks=%d failures=%d\n", checks, failures);
	if (failures) {
		printf("RESULT: FAIL\n");
		return 1;
	}
	printf("RESULT: PASS\n");
	return 0;
}
