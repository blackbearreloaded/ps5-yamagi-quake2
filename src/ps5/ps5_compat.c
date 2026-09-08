#include <stddef.h>

int if_nametoindex(const char *name)
{
	(void)name;
	return 0;
}

const char *nl_langinfo(int item)
{
	(void)item;
	return "UTF-8";
}

int ___mb_cur_max(void)
{
	return 1;
}
