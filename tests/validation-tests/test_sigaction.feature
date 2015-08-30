Feature: Slingshot yields valid results for the function under test sigaction

    Background:
        Given The function under test has the signature sigaction-signal-ptr_sigaction-ptr_sigaction

    Scenario: Running testcase 55693 of sigaction
        Given the specified testcase is 55693
        When running the testcase
        Then slingshot is detecting a ABORT
