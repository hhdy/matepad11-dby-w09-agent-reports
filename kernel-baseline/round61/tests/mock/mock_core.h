/* ROUND31/ROUND32 host test harness: minimal kernel API mock.
 * This is NOT kernel code. It exists only so that the real
 * drivers/regulator/proxy-consumer.c can be compiled and executed on the
 * host, which makes the proxy consumer lifecycle assertable instead of
 * merely greppable.
 *
 * ROUND32 additions: dev_of_node(), of_regulator_get() with node->rdev
 * resolution and -EPROBE_DEFER semantics, per-target vote recording and a
 * late_initcall capture alongside the late_initcall_sync capture.
 */
#ifndef MOCK_CORE_H
#define MOCK_CORE_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>
#include <errno.h>

typedef uint32_t u32;

#define GFP_KERNEL 0

#define __init
#define __must_check
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

/* ---------- err ---------- */
#define MAX_ERRNO 4095
#define EPROBE_DEFER 5
#define IS_ERR_VALUE(x) ((unsigned long)(void *)(x) >= (unsigned long)-MAX_ERRNO)
static inline void *ERR_PTR(long e) { return (void *)e; }
static inline long PTR_ERR(const void *p) { return (long)p; }
static inline bool IS_ERR(const void *p) { return IS_ERR_VALUE((unsigned long)p); }
static inline bool IS_ERR_OR_NULL(const void *p) { return !p || IS_ERR(p); }

/* ---------- list ---------- */
struct list_head {
	struct list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define LIST_HEAD(name) struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *l)
{
	l->next = l;
	l->prev = l;
}

static inline void __list_add(struct list_head *n, struct list_head *prev,
			      struct list_head *next)
{
	next->prev = n;
	n->next = next;
	n->prev = prev;
	prev->next = n;
}

static inline void list_add_tail(struct list_head *n, struct list_head *head)
{
	__list_add(n, head->prev, head);
}

static inline void list_del(struct list_head *e)
{
	e->prev->next = e->next;
	e->next->prev = e->prev;
	e->next = NULL;
	e->prev = NULL;
}

static inline int list_empty(const struct list_head *h)
{
	return h->next == h;
}

#define container_of(ptr, type, member) \
	((type *)((char *)(ptr) - (size_t)&(((type *)0)->member)))

#define list_entry(ptr, type, member) container_of(ptr, type, member)
#define list_first_entry(ptr, type, member) \
	list_entry((ptr)->next, type, member)

#define list_for_each_entry_safe(pos, n, head, member)			\
	for (pos = list_first_entry(head, __typeof__(*pos), member),	\
	     n = list_first_entry(&pos->member, __typeof__(*pos), member); \
	     &pos->member != (head);					\
	     pos = n, n = list_first_entry(&n->member, __typeof__(*n), member))

/* ---------- mutex ---------- */
struct mutex { int locked; };
#define DEFINE_MUTEX(m) struct mutex m = { 0 }
static inline void mutex_lock(struct mutex *m) { m->locked = 1; }
static inline void mutex_unlock(struct mutex *m) { m->locked = 0; }

/* ---------- alloc ---------- */
static inline void *kzalloc(size_t n, int f) { (void)f; return calloc(1, n); }
static inline void kfree(const void *p) { free((void *)p); }

/* ---------- device / of ---------- */
struct device {
	const char *name;
	struct device_node *of_node;
};

static inline const char *dev_name(const struct device *d)
{
	return d && d->name ? d->name : NULL;
}

static inline struct device_node *dev_of_node(struct device *d)
{
	return d ? d->of_node : NULL;
}

struct property {
	const char *name;
	int length;
	const void *value;
};

struct device_node {
	const char *full_name;
	struct property props[6];
	int nprops;
};

static inline struct property *of_find_property(const struct device_node *np,
						const char *name, int *lenp)
{
	int i;

	if (!np)
		return NULL;
	for (i = 0; i < np->nprops; i++) {
		if (!strcmp(np->props[i].name, name)) {
			if (lenp)
				*lenp = np->props[i].length;
			return (struct property *)&np->props[i];
		}
	}
	return NULL;
}

static inline bool of_property_present(const struct device_node *np,
				       const char *name)
{
	return of_find_property(np, name, NULL) != NULL;
}

/* Parse a single mock phandle and mirror the OF node reference contract. */
static inline struct device_node *
of_parse_phandle(const struct device_node *np, const char *name, int index)
{
	struct property *p;

	if (index)
		return NULL;
	p = of_find_property(np, name, NULL);
	if (!p || p->length != (int)sizeof(struct device_node *))
		return NULL;
	return (struct device_node *)p->value;
}

static inline void of_node_put(struct device_node *np) { (void)np; }

static inline int of_property_read_u32(const struct device_node *np,
				       const char *name, u32 *out)
{
	struct property *p = of_find_property(np, name, NULL);

	if (!p)
		return -2; /* -ENOENT */
	if (p->length != 4)
		return -22; /* -EINVAL */
	memcpy(out, p->value, 4);
	return 0;
}

static inline int of_property_read_u32_array(const struct device_node *np,
					     const char *name, u32 *out,
					     size_t n)
{
	struct property *p = of_find_property(np, name, NULL);

	if (!p)
		return -2;
	if ((size_t)p->length != n * 4)
		return -22;
	memcpy(out, p->value, p->length);
	return 0;
}

/* ---------- regulator ---------- */
struct regulator_dev;

struct proxy_consumer;

struct regulator_dev {
	struct proxy_consumer *proxy_consumer;
};

struct regulator {
	void *target;
};

/* ---------- mock instrumentation ---------- */
enum mock_action {
	MOCK_LOAD,
	MOCK_ENABLE,
	MOCK_DISABLE,
	MOCK_VOLTAGE,
	MOCK_PUT,
	MOCK_GET_OK,
	MOCK_GET_DEFER,
};

struct mock_vote {
	void *target;
	int action;
	int value;
	int minv;
	int maxv;
};

#define MOCK_VOTES_MAX 256

struct mock_stats {
	int get_calls;
	int put_calls;
	int enable_calls;
	int disable_calls;
	int set_load_calls;
	int set_voltage_calls;
	int enable_balance;
	int load_uA;
	int voltage_min;
	int voltage_max;
	int fail_set_load;
	int fail_enable;
	int fail_set_voltage;
	int last_get_id_is_proxy;
	struct mock_vote votes[MOCK_VOTES_MAX];
	int nvotes;
};

extern struct mock_stats mock;

static inline void mock_record(void *target, int action, int value,
			       int minv, int maxv)
{
	if (mock.nvotes >= MOCK_VOTES_MAX)
		return;
	mock.votes[mock.nvotes].target = target;
	mock.votes[mock.nvotes].action = action;
	mock.votes[mock.nvotes].value = value;
	mock.votes[mock.nvotes].minv = minv;
	mock.votes[mock.nvotes].maxv = maxv;
	mock.nvotes++;
}

static inline int mock_count(void *target, int action)
{
	int i, n = 0;

	for (i = 0; i < mock.nvotes; i++)
		if (mock.votes[i].target == target &&
		    mock.votes[i].action == action)
			n++;
	return n;
}

/* node -> rdev registry emulating "the target regulator is registered and
 * findable by its device node".  A phandle to a node without an entry
 * behaves like a not-yet-registered target: -EPROBE_DEFER.
 */
#define MOCK_TARGETS_MAX 8
static void *mock_target_node[MOCK_TARGETS_MAX];
static struct regulator_dev *mock_target_rdev[MOCK_TARGETS_MAX];
static int mock_ntargets;

static inline struct regulator_dev *mock_find_target(void *node)
{
	int i;

	for (i = 0; i < mock_ntargets; i++)
		if (mock_target_node[i] == node)
			return mock_target_rdev[i];
	return NULL;
}

static inline void mock_register_target(void *node, struct regulator_dev *rdev)
{
	mock_target_node[mock_ntargets] = node;
	mock_target_rdev[mock_ntargets] = rdev;
	mock_ntargets++;
}

static inline void mock_unregister_all_targets(void) { mock_ntargets = 0; }

static inline struct regulator *regulator_get(struct device *dev,
					      const char *id)
{
	struct device_node *target;
	struct regulator *r;

	mock.get_calls++;
	mock.last_get_id_is_proxy = id && !strcmp(id, "proxy");
	target = of_parse_phandle(dev ? dev->of_node : NULL, "proxy-supply", 0);
	if (!target || !mock_find_target(target)) {
		mock_record(target, MOCK_GET_DEFER, 0, 0, 0);
		return ERR_PTR(-EPROBE_DEFER);
	}
	r = calloc(1, sizeof(*r));
	if (!r)
		return NULL;
	r->target = target;
	mock_record(target, MOCK_GET_OK, 0, 0, 0);
	return r;
}

/* regulator-by-device-node, mirroring of_regulator_get() + the pinned
 * of_regulator_dev_lookup() contract: property present -> resolve phandle;
 * phandle target has no registered rdev -> -EPROBE_DEFER; no property ->
 * -ENODEV.
 */
static inline struct regulator *of_regulator_get(struct device *dev,
						 struct device_node *node,
						 const char *id)
{
	struct property *p;
	struct device_node *target;
	struct regulator_dev *rdev;
	struct regulator *r;

	(void)dev;
	mock.get_calls++;
	if (!node)
		return ERR_PTR(-ENODEV);
	p = of_find_property(node, "proxy-supply", NULL);
	if (!p)
		return ERR_PTR(-ENODEV);
	target = (struct device_node *)p->value;
	rdev = mock_find_target(target);
	if (!rdev) {
		mock_record(target, MOCK_GET_DEFER, 0, 0, 0);
		return ERR_PTR(-EPROBE_DEFER);
	}
	r = calloc(1, sizeof(struct regulator));
	if (!r)
		return NULL;
	r->target = (void *)target;
	mock_record(target, MOCK_GET_OK, 0, 0, 0);
	return r;
}

static inline void regulator_put(struct regulator *r)
{
	mock.put_calls++;
	if (r)
		mock_record(r->target, MOCK_PUT, 0, 0, 0);
	free(r);
}

static inline int regulator_enable(struct regulator *r)
{
	void *t = r ? r->target : NULL;

	mock.enable_calls++;
	if (mock.fail_enable)
		return mock.fail_enable;
	mock.enable_balance++;
	mock_record(t, MOCK_ENABLE, 0, 0, 0);
	return 0;
}

static inline int regulator_disable(struct regulator *r)
{
	void *t = r ? r->target : NULL;

	mock.disable_calls++;
	mock.enable_balance--;
	mock_record(t, MOCK_DISABLE, 0, 0, 0);
	return 0;
}

static inline int regulator_set_load(struct regulator *r, int uA)
{
	void *t = r ? r->target : NULL;

	mock.set_load_calls++;
	if (mock.fail_set_load)
		return mock.fail_set_load;
	mock.load_uA = uA;
	mock_record(t, MOCK_LOAD, uA, 0, 0);
	return 0;
}

static inline int regulator_set_voltage(struct regulator *r, int min, int max)
{
	void *t = r ? r->target : NULL;

	mock.set_voltage_calls++;
	if (mock.fail_set_voltage)
		return mock.fail_set_voltage;
	mock.voltage_min = min;
	mock.voltage_max = max;
	mock_record(t, MOCK_VOLTAGE, 0, min, max);
	return 0;
}

/* ---------- printk ---------- */
#define pr_err(fmt, ...)  printf("[pr_err] " fmt, ##__VA_ARGS__)
#define pr_info(fmt, ...) printf("[pr_info] " fmt, ##__VA_ARGS__)
#define dev_err(dev, fmt, ...) do { (void)(dev); printf("[dev_err] " fmt, ##__VA_ARGS__); } while (0)
#define dev_dbg(dev, fmt, ...) do { if (0) { (void)(dev); printf(fmt, ##__VA_ARGS__); } } while (0)

/* ---------- initcall capture ---------- */
extern int (*mock_late_initcall_fn)(void);
extern int (*mock_late_initcall_retry_fn)(void);
#define late_initcall_sync(fn) int (*mock_late_initcall_fn)(void) = fn
#define late_initcall(fn) int (*mock_late_initcall_retry_fn)(void) = fn

#endif /* MOCK_CORE_H */
