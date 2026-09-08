#ifndef YQ2_PS5_LIFECYCLE_H
#define YQ2_PS5_LIFECYCLE_H

void ps5_frame_start(void);
int ps5_frame_should_quit(void);
void ps5_record_present(void);
void ps5_record_failure(void);
int ps5_frame_stop(int status);
_Noreturn void ps5_exit(int status);

#endif
