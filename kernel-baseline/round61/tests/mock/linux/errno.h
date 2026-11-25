#ifndef _MOCK_ERRNO_H
#define _MOCK_ERRNO_H
/* minimal errno values used by the driver and mock (glibc-compatible).
 * This shim intercepts <linux/errno.h> so the kernel header does not leak
 * its own EPROBE_DEFER (517) into the host build.
 */
#ifndef EPERM
#define EPERM 1
#endif
#ifndef ENOENT
#define ENOENT 2
#endif
#ifndef EPROBE_DEFER
#define EPROBE_DEFER 5
#endif
#ifndef ENOMEM
#define ENOMEM 12
#endif
#ifndef ENODEV
#define ENODEV 19
#endif
#ifndef EINVAL
#define EINVAL 22
#endif
#endif
