# On the Job Training (OJT) Module – Workflow Overview

## 1. Job Preparation
Before using the OJT features, ensure that a job position is available for training.  
Any open recruitment position (e.g. *"Odoo Developer Trainee"*) can be linked to an OJT process.

To make it eligible:
- Go to **Recruitment → Configuration → Stages**
- Add the corresponding **Job Position** to the **On The Job Training Stage** list.

This marks the job as part of the On the Job Training workflow.

---

## 2. Applicant Enrollment
Once a job is configured for OJT:
- Applicants who reach the “On the Job Training” stage in recruitment will be automatically enrolled in the OJT process.
- When their stage is changed to **“On the Job Training”**, the system will:
  - Send an **email invitation** containing a signup link (if they don’t have an account yet).
  - Allow them to **log in** to the portal using existing credentials if they already have an account.

---

## 3. Portal Access
Participants can access their OJT dashboard via the **Odoo Portal**:
- From there, they can:
  - View available **Batches**
  - **Apply** to a specific batch
  - View and **submit assignments**
  - **Attend events** or training sessions
  - Track their **scores** and progress

---

## 4. Batch and Assignment Management
Each OJT batch is managed by mentors or administrators.

Typical workflow:
1. **Batch Creation** – Admin or mentor creates a new batch and defines its duration, description, and participants.
2. **Assignments** – Each batch contains one or more assignments that participants must complete.
3. **Submissions** – Participants upload or submit work through the portal.
4. **Scoring** – Mentors evaluate submissions and record scores.

---

## 5. Certificate Generation
When the **Batch Stage** changes to **“Done”**, the system automatically:
- Generates a **Certificate** for each participant in that batch.
- Calculates:
  - The **total number of assignments**
  - The **average score**
- Creates a **PDF certificate** with participant details, congratulatory message, and a **QR code**.

---

## 6. Certificate Access and Verification
Participants can:
- **Download their certificate** directly from the portal once the batch is marked as “Done”.
- Each certificate PDF includes a **QR code** that can be scanned by anyone to verify authenticity.

When scanned, the QR code redirects to a **public verification page** displaying:
- Participant name
- Batch information
- Certificate issue date
- Validation status

---

## 7. Access Control
- **Administrators and Mentors** can manage all OJT data:
  - Batches, Participants, Assignments, Submissions, Events, and Certificates.
- **Participants** (portal users) can only:
  - View their assigned batches and tasks
  - Submit assignments
  - View their attendance and certificates

---

## Summary

| Role | Capabilities |
|------|---------------|
| **Admin/Mentor** | Create batches, manage participants, issue certificates |
| **Participant (Portal User)** | Join batch, submit assignments, attend events, download certificate |
| **Public User** | Verify certificate authenticity via QR code |

---

## End of Workflow
The OJT process completes when all participants in a batch have received their certificates and verification is available publicly.
