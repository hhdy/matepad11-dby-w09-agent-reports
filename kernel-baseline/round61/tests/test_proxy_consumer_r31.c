/* ROUND31 executable lifecycle test for drivers/regulator/proxy-consumer.c
 *
 * The real driver source is compiled into this harness through the mock tree
 * in tests/mock, so the assertions below exercise the shipped code rather
 * than a reimplementation of it.
 */
#include <mock_core.h>

struct mock_stats mock;
int (*mock_late_initcall_fn)(void);

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

static void del_props(struct device_node *np)
{
	int i;

	for (i = 0; i < np->nprops; i++)
		if ((np->props[i].length == 4 || np->props[i].length == 8) &&
		    np->props[i].value)
			free((void *)np->props[i].value);
	np->nprops = 0;
}

int main(void)
{
	struct device_node l5 = { .full_name = "/pm8150-rpmh-regulators/ldo5" };
	struct device_node l9 = { .full_name = "/pm8150-rpmh-regulators/ldo9" };
	struct device group = { .name = "pm8150-rpmh-regulators" };
	struct regulator_dev rdev5 = { 0 };
	struct regulator_dev rdev9 = { 0 };
	struct proxy_consumer *c;

	printf("== ROUND31 proxy-consumer lifecycle test ==\n");

	/* 1. no properties: nothing happens at all */
	reset_mock();
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(c == NULL, "no proxy properties -> NULL consumer");
	CHECK(mock.get_calls == 0, "no proxy properties -> no regulator_get");
	CHECK(rdev5.proxy_consumer == NULL, "no proxy properties -> rdev untouched");

	/* 2. enable + current: exactly one get, one load vote, one enable */
	reset_mock();
	add_flag(&l5, "qcom,proxy-consumer-enable");
	add_u32(&l5, "qcom,proxy-consumer-current", 100000);
	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer), "enable+current -> consumer registered");
	CHECK(mock.get_calls == 1, "exactly one regulator_get");
	CHECK(mock.last_get_id_is_proxy == 1, "supply id is \"proxy\"");
	CHECK(mock.set_load_calls == 1 && mock.load_uA == 100000,
	      "single 100000 uA load vote");
	CHECK(mock.enable_calls == 1 && mock.enable_balance == 1,
	      "single enable, balance 1");

	/* 3. per-regulator unregister balances every vote */
	{
		int d0 = mock.disable_calls;
		int p0 = mock.put_calls;

		regulator_proxy_consumer_unregister(&rdev5);
		CHECK(rdev5.proxy_consumer == NULL,
		      "unregister clears rdev->proxy_consumer");
		CHECK(mock.disable_calls - d0 == 1 && mock.enable_balance == 0,
		      "unregister disables once, balance 0");
		CHECK(mock.load_uA == 0, "unregister drops load vote to 0");
		CHECK(mock.put_calls - p0 == 1, "unregister puts the regulator once");
	}

	/* 4. double unregister is a no-op, not double disable */
	reset_mock();
	regulator_proxy_consumer_unregister(&rdev5);
	CHECK(mock.disable_calls == 0 && mock.put_calls == 0,
	      "second unregister is a no-op");

	/* 5. current above INT_MAX is rejected before any regulator_get */
	reset_mock();
	del_props(&l5);
	add_u32(&l5, "qcom,proxy-consumer-current", 0x80000000u);
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "current > INT_MAX -> -EINVAL");
	CHECK(mock.get_calls == 0, "rejected before regulator_get");
	CHECK(rdev5.proxy_consumer == NULL, "rejected -> rdev untouched");

	/* 6. non-empty enable flag is rejected (type error) */
	reset_mock();
	del_props(&l5);
	add_u32(&l5, "qcom,proxy-consumer-enable", 1);
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "non-empty enable -> -EINVAL");
	CHECK(mock.get_calls == 0, "type error rejected before regulator_get");

	/* 7. inverted voltage range is rejected */
	reset_mock();
	del_props(&l5);
	add_u32_pair(&l5, "qcom,proxy-consumer-voltage", 1200000, 900000);
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "min > max voltage -> -EINVAL");

	/* 8. properties present but no actual request is rejected */
	reset_mock();
	del_props(&l5);
	add_u32(&l5, "qcom,proxy-consumer-current", 0);
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -22, "zero-only request -> -EINVAL");
	CHECK(mock.get_calls == 0, "zero-only request never touches a regulator");

	/* 9. set_load failure rolls back without enabling */
	reset_mock();
	del_props(&l5);
	add_flag(&l5, "qcom,proxy-consumer-enable");
	add_u32(&l5, "qcom,proxy-consumer-current", 100000);
	mock.fail_set_load = -5;
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -5, "set_load failure propagates");
	CHECK(mock.enable_calls == 0 && mock.enable_balance == 0,
	      "set_load failure -> no enable");
	CHECK(mock.put_calls == 1, "set_load failure -> regulator_put once");
	CHECK(rdev5.proxy_consumer == NULL, "failed registration leaves rdev clean");

	/* 10. enable failure unwinds the load vote */
	reset_mock();
	mock.fail_enable = -6;
	c = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -6, "enable failure propagates");
	CHECK(mock.load_uA == 0, "enable failure restores load to 0");
	CHECK(mock.put_calls == 1, "enable failure -> regulator_put once");

	/* 11. two rails, bulk late_initcall_sync removal */
	reset_mock();
	del_props(&l5);
	add_flag(&l9, "qcom,proxy-consumer-enable");
	add_u32(&l9, "qcom,proxy-consumer-current", 100000);
	add_flag(&l5, "qcom,proxy-consumer-enable");
	add_u32(&l5, "qcom,proxy-consumer-current", 100000);
	rdev5.proxy_consumer = regulator_proxy_consumer_register(&group, &l5, &rdev5);
	rdev9.proxy_consumer = regulator_proxy_consumer_register(&group, &l9, &rdev9);
	CHECK(!IS_ERR_OR_NULL(rdev5.proxy_consumer) &&
	      !IS_ERR_OR_NULL(rdev9.proxy_consumer), "two rails registered");
	CHECK(mock.enable_balance == 2, "two rails -> enable balance 2");

	{
		int d0 = mock.disable_calls;
		int p0 = mock.put_calls;
		int l0 = mock.set_load_calls;

		CHECK(mock_late_initcall_fn != NULL, "late_initcall_sync hook captured");
		mock_late_initcall_fn();
		CHECK(mock.disable_calls - d0 == 2 && mock.enable_balance == 0,
		      "late_initcall_sync drops both enables");
		CHECK(mock.set_load_calls - l0 == 2 && mock.load_uA == 0,
		      "late_initcall_sync drops both load votes");
		CHECK(mock.put_calls - p0 == 2,
		      "late_initcall_sync puts both regulators");
	}
	CHECK(rdev5.proxy_consumer == NULL && rdev9.proxy_consumer == NULL,
	      "late_initcall_sync clears both back-pointers");

	/* 12. second bulk removal is a no-op */
	{
		int d0 = mock.disable_calls;
		int p0 = mock.put_calls;

		mock_late_initcall_fn();
		CHECK(mock.disable_calls == d0 && mock.put_calls == p0,
		      "second late_initcall_sync is a no-op");
	}

	/* 13. registration after the bulk removal is refused */
	reset_mock();
	del_props(&l9);
	add_flag(&l9, "qcom,proxy-consumer-enable");
	c = regulator_proxy_consumer_register(&group, &l9, &rdev9);
	CHECK(IS_ERR(c) && PTR_ERR(c) == -1, "registration after removal -> -EPERM");
	CHECK(mock.get_calls == 0, "refused registration does not vote");

	del_props(&l5);
	del_props(&l9);

	printf("\nchecks=%d failures=%d\n", checks, failures);
	if (failures) {
		printf("RESULT: FAIL\n");
		return 1;
	}
	printf("RESULT: PASS\n");
	return 0;
}
