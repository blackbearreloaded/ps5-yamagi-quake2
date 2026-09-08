#include "../../upstream/yquake2/src/client/vid/header/ref.h"

extern refexport_t GetRefAPI(refimport_t import);

refexport_t
PS5_GetRefAPI(refimport_t import)
{
	return GetRefAPI(import);
}
