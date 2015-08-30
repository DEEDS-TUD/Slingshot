Feature: Slingshot should yield valid results for the function under test getcwd

    Background:
        Given The function under test has the signature getcwd-ptr_char-int

    Scenario: Running testcase 429 of getcwd
        Given the specified testcase is 429
        When running the testcase
        Then slingshot is detecting a PASS

