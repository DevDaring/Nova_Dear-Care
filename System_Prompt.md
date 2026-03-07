Old_Code folder contains previous code that was run on RDK X5
You need to understand that.
Currently I will run code on RDK S100
System spec has been written on RDK_System_Info.md . Understand that.
Understand that the RDK S100 platform is being used for the Pocket ASHA system, which differs from the previous RDK X5 platform. The system specifications for RDK S100 are detailed in RDK_System_Info.md, which includes information about the OS, kernel, and other relevant components. The design of the Pocket ASHA system is described in pocket-asha/design.md, highlighting its multimodal capabilities and integration with various hardware and software components.
Under system design from requirements.md
You need to write full codes in Code folder.
Write code in such a way that is one or more sensor not detected or throw error its should work.
I will use AWS lambda to store my agentic program.
This is for AWS Hackathon AI for Bharat so I will use some Amazon models and amazon services for most of the online part. No google services will be used.
I will provide all keys in .env file in Code folder.
You can use all required aws keys from .env
You should use those keys in code with loadenv command
You can use those aws keys to setup in aws lambda.
Main agentic code will run on aws lambda
I have already created env.template for your understanding.
You should create this files in Code folder.
If intnet is not not available it will store information in local.
Understand the constraint of sdk s100. This should not hanged or memory should not overflown.

