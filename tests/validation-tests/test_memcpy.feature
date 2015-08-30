Feature: Slingshot yields valid results for the function under test memcpy

    Background:
        Given The function under test has the signature memcpy-ptr_char-ptr_char-unsigned_long

    Scenario: Running testcase 42602 of memcpy
        Given the specified testcase is 42602
        When running the testcase
        Then slingshot is detecting a PASS
