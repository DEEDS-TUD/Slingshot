#include <assert.h>  //for asserts in manage_test
#include <dlfcn.h>  //for dynamic loading in constructor
#include <iostream>  //for cout and cerr
#include <signal.h>  //for SIGKILL
#include <stdio.h>  //generally needed
#include <stdlib.h>  //generally needed
#include <string.h>  //for strncpy, strcat, strstr in manage_test
#include <sys/types.h>  //for pid_t and other types
#include <sys/time.h>
#include <sys/wait.h>  //for waitpid
#include <unistd.h>  //generally needed, fork, process stuff
#include <errno.h>   //added 11/16/99 for error reporting

long long get_time_in_microseconds(void);
char *safe_strncpy(char *, const char *, size_t);

#define TEMP_BUF_SIZE 1024

#define RVAL_STRING "rval:"

#define READING_PIPE_FAILED -7
#define MALLOC_FAILED -6
#define PIPE_FAILED -5
#define UNDEFINED_RESULT -4
#define WAITPID_FAILED -3
#define MARSHAL_STRING_FAILED -2
#define FORK_FAILED -1
#define RETURN_OK 0


/* List of signals which produce core dumps, (man 7 signal)
SIGQUIT       3       Core    Quit from keyboard
SIGILL        4       Core    Illegal Instruction
SIGABRT       6       Core    Abort signal from abort(3)
SIGFPE        8       Core    Floating point exception
SIGSEGV      11       Core    Invalid memory reference
SIGBUS      10,7,10     Core    Bus error (bad memory access)
SIGSYS      12,31,12    Core    Bad argument to routine (SVr4)
SIGTRAP        5        Core    Trace/breakpoint trap
SIGXCPU     24,24,30    Core    CPU time limit exceeded (4.2BSD)
SIGXFSZ     25,25,31    Core    File size limit exceeded (4.2BSD)
SIGIOT         6        Core    IOT trap. A synonym for SIGABRT
SIGUNUSED    -,31,-     Core    Synonymous with SIGSYS
*/
static int core_dumping_signal[] = { 3, 4, 5, 6, 7, 8, 10, 11, 12, 24, 25, 30, 31 };

int main (int argc, char* argv[])
{
  void *handle;  //handle for dynamically loaded file
  pid_t pid;
  long long timeout_value = 5000000;
  int (*test_exec_ptr)(); // function ptr to testcase

  char *errstr;
  // Path to the shared lib under test
  char *module_under_test = argv[1];

  dlerror(); // clear old errors
  // Open handle to testcase file
  if (!(handle = dlopen(module_under_test, RTLD_NOW | RTLD_GLOBAL))) {
    errstr = dlerror();
    if (errstr != NULL)
    printf ("A dynamic linking error occurred: (%s)\n", errstr);
    abort();
  }

  dlerror(); // clear old errors
  *(void **) (&test_exec_ptr) = dlsym(handle, "exec_tc");
  if ((errstr = dlerror()) != NULL) {
    printf ("A dynamic linking error occurred: (%s)\n", errstr);
    abort();
  }

  pid = 0;

  int status = 0;  //Status of forked process
  pid_t wait_pid_return = 0;  // Return value of waitpid
  int pipe_file_desc [2]; //file descriptors for pipe between parent & child
  FILE * mut_output;
  char * temp_mut_return = NULL; //temporary string to hold piped output
  char * mut_return_start = NULL; //pointer to actual return value from mut
  long long start_time = 0;
  long long timeout = timeout_value;

  int num_matching = 0; // how many characters did we match out of 'rval:'
  int num_to_match = 0; // how many characters must we match
  const char *string_to_match = NULL;  // string to match against
  int c = 0;  // character read from file
  int bytes_read = 0; // number of bytes read from pipe

  // TODO: The following vars are from the function signautre
  //char *mut_return;
  char mut_return[2048];
  //int max_mut_return;
  int max_mut_return = sizeof(mut_return);
  //int *call_ret;
  int c_ret;
  int *call_ret = &c_ret;
  //char *pass_status;
  char pass_status[255];
  // TODO: max_pass_staus has to be > 0 if safe-strcpy should do anything!!
  //int max_pass_status;
  int max_pass_status = sizeof(pass_status);
  // TODO: SET max_sys_err to 255 -> 
  //char *sys_err;
  char sys_err[255];
  int max_sys_err = sizeof(sys_err);
  // TODO: END

  struct sigaction action; //signal-handling struct

  //set up pipe for communication between parent and child processes
  if (pipe (pipe_file_desc) < 0) {
    std::cerr << "Pipe Failed" << std::endl;
    return PIPE_FAILED;
  }

  // Fork off a process and check for errors
  if ((pid = fork()) < 0) {
    std::cerr << "Fork Failed." << std::endl;
    return FORK_FAILED;
  }

  else if (pid == 0) {  //child process to execute test
    // write debug messages to a logfile
    FILE* child_log = NULL;
    if ((child_log = fopen("/tmp/child.log", "a+")) == NULL) {
        std::cout << "Could not open child log" << std::endl;
    }

    close(pipe_file_desc[0]);
    //redirect Output only from this child to the pipe
    dup2 (pipe_file_desc[1], STDOUT_FILENO); //stdout

    // remove signal handlers that were installed
    sigemptyset (&action.sa_mask);
    action.sa_handler = SIG_DFL;
    (void) sigaction (SIGINT, &action, NULL);
    (void) sigaction (SIGQUIT, &action, NULL);
    (void) sigaction (SIGTERM, &action, NULL);
    (void) sigaction (SIGABRT, &action, NULL);

    int exec_tc_ret;
    exec_tc_ret = (*test_exec_ptr)();
    fprintf(child_log, "exec_tc_ret: %d\n", exec_tc_ret);
     // Close logfile
    //fclose(child_log);
    exit(exec_tc_ret); //exits with errno status
  }  //end child process

 //parent process to monitor child
  close(pipe_file_desc[1]);
  mut_output = fdopen(pipe_file_desc[0], "r");

  start_time = get_time_in_microseconds();

  while(start_time + timeout > get_time_in_microseconds())  {
    wait_pid_return = waitpid (pid, &status, WNOHANG);

    //check if waitpid error
    if (wait_pid_return < 0) {
      std::cerr << "Error waiting for child process.  Child %d " << pid;
      std::cerr << "does not exist, its group does not exist," << std::endl;
      std::cerr << "or the process is not a child of the Test Manager." << std::endl;
      return WAITPID_FAILED;
    }
    // check if process terminated
    if(wait_pid_return > 0) {
      pid = 0;  //signal to parent child no longer exists
      break;
    }

    // sleep for 500 microseconds before checking again
    usleep(500);   
  } //end while

  // check that the loop terminated because the process terminated
  if (wait_pid_return > 0) {
    pid = 0;

    // read one character at a time from the pipe.
    // keep checking against RVAL_STRING to see if we match
    // after we match, copy up until max_mut_return-1 characters into 
    // mut_return.  Then NULL terminate mut_return.  Finally remove the
    // last carriage return in mut_return.  That '\n' comes from 
    // execute_test_case

    num_matching = 0;
    num_to_match = strlen(RVAL_STRING);
    string_to_match = RVAL_STRING;

    while((c = fgetc(mut_output)) != EOF) {
      if(c == string_to_match[num_matching]) {
        num_matching++;
        if(num_matching == num_to_match) {
          // we've found 'rval:', now read in the rest
          bytes_read = fread(mut_return,
                             sizeof(char), 
                             max_mut_return-1,
                             mut_output);

          if((bytes_read < 0) || (bytes_read > max_mut_return-1)) {
            std::cerr << "Error reading from pipe." << std::endl;
            return READING_PIPE_FAILED;
          }
          mut_return[bytes_read] = '\0'; // null terminate

          // take out trailing carriage return if it is there
          if(bytes_read > 0) {
            if(mut_return[bytes_read - 1] == '\n') {
              mut_return[bytes_read - 1] = '\0';
            }
          }
          break;
        }
      }
      else {  // we didn't match this char, so reset the count
        num_matching = 0;
      }
    }


    fclose(mut_output);

    // process has terminated, either a Pass or an Abort has occurred
    if (WIFSIGNALED(status)) {
      // Check if child has produced a core dump
      int received_signal = WTERMSIG(status);
      int has_dumped = 0;
      for (int i = 0; i < (sizeof(core_dumping_signal)/sizeof(int)); i++) {
        if (core_dumping_signal[i] == received_signal) {
            has_dumped = 1;
            break;
        }
      }
      if (has_dumped) {
          // uhh smelly...
          *call_ret = -1;
          std::cout << "ABORT_DUMPED";
      } else {
          *call_ret = -1;
          std::cout << "ABORT";
          safe_strncpy(pass_status, "Done - Abort", max_pass_status);
      }
    }
    else if (WIFEXITED(status)) {
      *call_ret = WEXITSTATUS(status);
      if (*call_ret == 99)
      {
        std::cout << "SETUP" << std::endl;
        safe_strncpy(pass_status, "Done - Setup Failed", max_pass_status);
      }
      else
      {
        std::cout << "PASS" << std::endl;
        safe_strncpy(pass_status, "Done - Pass", max_pass_status);
      }
      if (*call_ret >= 0) {
        // Copy error message string for reporting. added 11/16/99
        safe_strncpy(sys_err, sys_errlist[*call_ret], max_sys_err);
      }
    }
    else if (WIFSTOPPED(status)) {
      *call_ret = -1;
      std::cout << "STOPPED" << std::endl;
      safe_strncpy(pass_status, "Done - Stopped", max_pass_status);
    }
    else { //something has gone wrong, we should never fall through here
      std::cerr << "UNDEF" << std::endl;
      return UNDEFINED_RESULT;
    }
  } //end if process termination ended loop
  else {
    // did not terminate, clean up child processes
    kill (pid, SIGKILL);
    *call_ret = waitpid (pid, &status, 0);
    pid = 0;
    std::cout << "RESTART" << std::endl;
    safe_strncpy(pass_status, "RESTART", max_pass_status);
  } 

  return RETURN_OK;
}

void cleanup(pid_t pid) {
  if (pid != 0) {
    // clean up child process
    kill (pid, SIGTERM);
    waitpid (pid, NULL, 0);  //we don't care about status, so we use NULL
  }
}

long long get_time_in_microseconds(void)
{
  struct timeval timeofday;
  struct timezone tz;
  long long time;

  if(gettimeofday(&timeofday,&tz) != 0) {
    std::cerr << "Error getting time." << std::endl;
    exit(-100);
  }
  time = timeofday.tv_sec;
  time *= 1000000;
  time += timeofday.tv_usec;
  return time;
}

char *safe_strncpy(char *dst, const char *src, size_t n)
{
  assert(dst != NULL);

  if(n > 0) {
    dst[n-1] = 0;
    return strncpy(dst,src,n-1);
  }
  else
    return dst;
}
